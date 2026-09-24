"""
Ledger service — the ONLY sanctioned way to post to the double-entry ledger.

`post_transaction` is atomic (all entries or none) and idempotent (replaying an
idempotency key returns the existing transaction). It refuses to post an
unbalanced set of entries, so the books can never drift.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from django.db import transaction as db_transaction, IntegrityError

from .models_ledger import LedgerAccount, LedgerTransaction, LedgerEntry
from .references import generate_reference, Platform


@dataclass(frozen=True)
class Posting:
    """One leg of a balanced transaction."""
    account_code: str
    amount: int          # signed minor units (+credit / -debit)
    currency: str = "EGP"


class LedgerError(Exception):
    pass


class UnbalancedTransaction(LedgerError):
    pass


def post_transaction(
    *,
    idempotency_key: str,
    postings: Sequence[Posting],
    platform_code: str = Platform.CAREER,
    description: str = "",
    context: dict | None = None,
) -> LedgerTransaction:
    """Atomically post a balanced set of entries.

    - Sum of posting amounts MUST be zero (double-entry invariant).
    - Replaying the same `idempotency_key` returns the existing transaction and
      does NOT post again.
    """
    if not postings:
        raise UnbalancedTransaction("A transaction needs at least two postings")
    total = sum(p.amount for p in postings)
    if total != 0:
        raise UnbalancedTransaction(f"Postings must sum to 0, got {total}")

    # Fast path: already posted under this key.
    existing = LedgerTransaction.objects.filter(idempotency_key=idempotency_key).first()
    if existing:
        return existing

    try:
        with db_transaction.atomic():
            txn = LedgerTransaction.objects.create(
                reference=generate_reference(platform_code),
                platform_code=platform_code,
                description=description,
                idempotency_key=idempotency_key,
                context=context or {},
            )
            # Resolve accounts once; missing account is a hard error.
            for p in postings:
                account = LedgerAccount.objects.select_for_update().get(code=p.account_code)
                LedgerEntry.objects.create(
                    transaction=txn, account=account,
                    amount=p.amount, currency=p.currency,
                )
            return txn
    except IntegrityError:
        # A concurrent request won the idempotency race — return the winner.
        winner = LedgerTransaction.objects.filter(idempotency_key=idempotency_key).first()
        if winner:
            return winner
        raise


def get_or_create_account(code: str, *, name: str, kind: str,
                          currency: str = "EGP", owner_user=None) -> LedgerAccount:
    account, _ = LedgerAccount.objects.get_or_create(
        code=code,
        defaults={"name": name, "kind": kind, "currency": currency, "owner_user": owner_user},
    )
    return account
