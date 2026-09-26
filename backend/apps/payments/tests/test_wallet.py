"""
Ledger-backed wallet: derived balance, credit/debit, overdraw refusal, idempotency.
"""
import pytest
from django.contrib.auth import get_user_model

from apps.payments import wallet
from apps.payments.models import LedgerAccount

User = get_user_model()
pytestmark = pytest.mark.django_db


def test_wallet_credit_debit_derived_balance():
    u = User.objects.create_user(email="w@t.com", password="x")
    assert wallet.balance(u) == 0
    wallet.credit(user=u, amount=10000, idempotency_key="c1", reason="promo")
    assert wallet.balance(u) == 10000
    wallet.debit(user=u, amount=4000, idempotency_key="d1", reason="purchase")
    assert wallet.balance(u) == 6000


def test_wallet_credit_is_idempotent():
    u = User.objects.create_user(email="w2@t.com", password="x")
    wallet.credit(user=u, amount=5000, idempotency_key="same", reason="x")
    wallet.credit(user=u, amount=5000, idempotency_key="same", reason="x")  # replay
    assert wallet.balance(u) == 5000  # not doubled


def test_wallet_refuses_overdraw():
    u = User.objects.create_user(email="w3@t.com", password="x")
    wallet.credit(user=u, amount=1000, idempotency_key="c3", reason="x")
    with pytest.raises(ValueError):
        wallet.debit(user=u, amount=5000, idempotency_key="d3", reason="too much")


def test_wallet_balance_is_ledger_derived():
    u = User.objects.create_user(email="w4@t.com", password="x")
    wallet.credit(user=u, amount=7000, idempotency_key="c4", reason="x")
    acct = LedgerAccount.objects.get(code=f"wallet:user:{u.id}:egp")
    assert acct.balance() == 7000
    assert acct.kind == "liability"
