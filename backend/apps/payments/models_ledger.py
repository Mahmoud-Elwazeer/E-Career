"""
Double-entry ledger (directive Part XIV).

Design rules:
  * A balance is NEVER a mutable column. It is DERIVED from immutable
    LedgerEntry rows. There is no `account.balance = account.balance + x`.
  * Every money movement is a LedgerTransaction with >= 2 LedgerEntry rows
    whose signed amounts sum to exactly zero (balanced double entry).
  * Posting is atomic and idempotent: a caller supplies an idempotency key;
    replaying the same key returns the existing transaction instead of
    creating a duplicate (directive Part XIX).

Amounts are stored in MINOR units (integer piastres/cents) to avoid float
error. `currency` is ISO-4217 (e.g. "EGP", "USD").
"""
from __future__ import annotations

from django.db import models, transaction as db_transaction
from django.core.exceptions import ValidationError

from apps.core.models import UUIDModel
from .references import Platform


class LedgerAccount(UUIDModel):
    """A named account money flows between (assets, revenue, wallets, …)."""

    class Kind(models.TextChoices):
        ASSET = "asset", "Asset"            # e.g. cash-in-provider
        LIABILITY = "liability", "Liability"  # e.g. user wallet balance owed
        REVENUE = "revenue", "Revenue"
        REFUND = "refund", "Refund"
        FEES = "fees", "Fees"
        ESCROW = "escrow", "Escrow"

    code = models.CharField(max_length=100, unique=True, db_index=True,
                            help_text="Stable machine code, e.g. 'revenue:career'")
    name = models.CharField(max_length=150)
    kind = models.CharField(max_length=20, choices=Kind.choices)
    currency = models.CharField(max_length=3, default="EGP")
    # Optional owner linkage (a user/employer wallet account).
    owner_user = models.ForeignKey(
        "accounts.User", null=True, blank=True, on_delete=models.SET_NULL,
        related_name="ledger_accounts",
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "payments_ledger_account"
        ordering = ["code"]

    def __str__(self):
        return f"{self.code} ({self.currency})"

    def balance(self) -> int:
        """Derived balance in minor units — the sum of all posted entries."""
        agg = self.entries.aggregate(total=models.Sum("amount"))
        return int(agg["total"] or 0)


class LedgerTransaction(UUIDModel):
    """An atomic, balanced group of entries representing one money movement."""

    reference = models.CharField(max_length=40, unique=True, db_index=True)
    platform_code = models.CharField(max_length=1, choices=Platform.CHOICES,
                                     default=Platform.CAREER, db_index=True)
    description = models.CharField(max_length=255, blank=True)
    # Idempotency: the same key must never post twice.
    idempotency_key = models.CharField(max_length=120, unique=True, db_index=True)
    # Free-form link back to the business object that caused this (order id…).
    context = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = "payments_ledger_transaction"
        ordering = ["-created_at"]

    def __str__(self):
        return self.reference

    def is_balanced(self) -> bool:
        agg = self.entries.aggregate(total=models.Sum("amount"))
        return int(agg["total"] or 0) == 0


class LedgerEntry(UUIDModel):
    """An immutable signed posting to one account within a transaction.

    Positive `amount` credits the account balance; negative debits it. Entries
    are never updated or deleted — corrections are made with a reversing
    transaction.
    """

    transaction = models.ForeignKey(LedgerTransaction, on_delete=models.PROTECT,
                                    related_name="entries")
    account = models.ForeignKey(LedgerAccount, on_delete=models.PROTECT,
                                related_name="entries")
    amount = models.BigIntegerField(help_text="Signed minor units; + credit, - debit")
    currency = models.CharField(max_length=3, default="EGP")
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = "payments_ledger_entry"
        ordering = ["created_at"]
        indexes = [models.Index(fields=["account", "created_at"], name="ledger_entry_acct_idx")]

    def __str__(self):
        return f"{self.account.code} {self.amount:+d} {self.currency}"


class IdempotencyKey(UUIDModel):
    """Records a completed money-moving operation so retries are no-ops.

    Complements the unique key on LedgerTransaction for non-ledger operations
    (payment creation, webhook processing) that must also be idempotent.
    """

    key = models.CharField(max_length=160, unique=True, db_index=True)
    scope = models.CharField(max_length=60, db_index=True,
                             help_text="e.g. 'payment.create', 'webhook.process'")
    result_ref = models.CharField(max_length=120, blank=True,
                                  help_text="Reference of the object produced")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "payments_idempotency_key"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.scope}:{self.key}"
