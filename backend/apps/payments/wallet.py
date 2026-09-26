"""
Ledger-backed platform-credit wallet (directive Part XX).

A wallet is NOT a mutable balance column. It is a per-user liability
`LedgerAccount` (`wallet:user:<uuid>:<currency>`); the balance is DERIVED by
summing that account's immutable ledger entries. Credits/debits are balanced
double-entry postings against a platform wallet-funding account.

Scope (per product decision): PLATFORM CREDIT only — used to pay for packages.
No escrow, no payouts, no withdrawal to cash (those belong to Freelancing if/when
that product needs them). Credit is not withdrawable money.
"""
from __future__ import annotations

from .ledger import post_transaction, Posting, get_or_create_account


def _wallet_code(user, currency: str) -> str:
    return f"wallet:user:{user.id}:{currency.lower()}"


def ensure_wallet(user, currency: str = "EGP"):
    """Ensure the user's wallet ledger account (liability) + funding account exist."""
    acct = get_or_create_account(
        _wallet_code(user, currency),
        name=f"Wallet — {getattr(user, 'email', user.id)} ({currency})",
        kind="liability", currency=currency, owner_user=user,
    )
    get_or_create_account(
        f"wallet:funding:{currency.lower()}",
        name=f"Wallet funding ({currency})", kind="asset", currency=currency,
    )
    return acct


def balance(user, currency: str = "EGP") -> int:
    acct = ensure_wallet(user, currency)
    return acct.balance()


def credit(*, user, amount: int, currency: str = "EGP", idempotency_key: str,
           reason: str = "", platform_code: str = "C"):
    """Add platform credit to a user's wallet (balanced double entry)."""
    if int(amount) <= 0:
        raise ValueError("Credit amount must be positive")
    ensure_wallet(user, currency)
    return post_transaction(
        idempotency_key=idempotency_key,
        platform_code=platform_code,
        description=f"Wallet credit: {reason}"[:255],
        context={"user_id": str(user.id), "kind": "wallet_credit", "reason": reason},
        postings=[
            Posting(account_code=_wallet_code(user, currency), amount=int(amount), currency=currency),
            Posting(account_code=f"wallet:funding:{currency.lower()}", amount=-int(amount), currency=currency),
        ],
    )


def debit(*, user, amount: int, currency: str = "EGP", idempotency_key: str,
          reason: str = "", platform_code: str = "C"):
    """Spend platform credit. Refuses to overdraw the wallet."""
    amount = int(amount)
    if amount <= 0:
        raise ValueError("Debit amount must be positive")
    if balance(user, currency) < amount:
        raise ValueError("Insufficient wallet balance")
    return post_transaction(
        idempotency_key=idempotency_key,
        platform_code=platform_code,
        description=f"Wallet debit: {reason}"[:255],
        context={"user_id": str(user.id), "kind": "wallet_debit", "reason": reason},
        postings=[
            Posting(account_code=_wallet_code(user, currency), amount=-amount, currency=currency),
            Posting(account_code=f"wallet:funding:{currency.lower()}", amount=amount, currency=currency),
        ],
    )


def history(user, currency: str = "EGP", limit: int = 100):
    """Return the user's wallet ledger entries (derived history)."""
    acct = ensure_wallet(user, currency)
    return [
        {
            "amount": e.amount,
            "currency": e.currency,
            "reference": e.transaction.reference,
            "description": e.transaction.description,
            "created_at": e.created_at,
        }
        for e in acct.entries.select_related("transaction").order_by("-created_at")[:limit]
    ]
