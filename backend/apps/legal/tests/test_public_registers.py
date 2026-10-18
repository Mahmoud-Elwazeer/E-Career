"""
Public processor / data-transfer register endpoints — tests.

Added in the 2026-09-21 continuation pass to close a real gap: the
ProcessorRecord/DataTransferRecord models and their seed data already
existed, but were only ever exposed through the admin-gated API — there
was no public page/endpoint a prospective data subject could actually read
(the supplemental legal specs explicitly require a public sub-processor
disclosure and international-transfer disclosure page). These tests confirm
the new public, read-only, field-filtered endpoints that back
/legal/subprocessors and /legal/international-transfers.
"""
import pytest
from django.core.management import call_command
from rest_framework.test import APIClient

from apps.legal.models import ProcessorRecord, DataTransferRecord

pytestmark = pytest.mark.django_db


def test_processor_register_public_endpoint_is_unauthenticated_and_lists_seeded_vendors():
    call_command("seed_legal")
    resp = APIClient().get("/api/v1/legal/processors/")
    assert resp.status_code == 200
    names = {row["name"] for row in resp.json()["data"]}
    assert "Amazon Web Services (AWS)" in names
    assert "Stripe, Inc." in names


def test_processor_register_public_endpoint_excludes_internal_fields():
    """contract_reference and notes are internal procurement fields — never
    exposed on the public register, even though they exist on the model."""
    call_command("seed_legal")
    resp = APIClient().get("/api/v1/legal/processors/")
    assert resp.status_code == 200
    for row in resp.json()["data"]:
        assert "contract_reference" not in row
        assert "notes" not in row
        # dpa_signed IS exposed — the whole point of this page is showing
        # that DPA confirmation status honestly (including NULL).
        assert "dpa_signed" in row


def test_processor_register_public_endpoint_hides_inactive_records():
    call_command("seed_legal")
    hidden = ProcessorRecord.objects.first()
    hidden.is_active = False
    hidden.save(update_fields=["is_active"])
    resp = APIClient().get("/api/v1/legal/processors/")
    names = {row["name"] for row in resp.json()["data"]}
    assert hidden.name not in names


def test_data_transfer_register_public_endpoint_never_exposes_authorization_reference():
    processor = ProcessorRecord.objects.create(name="Test Vendor")
    DataTransferRecord.objects.create(
        processor=processor, destination_country="United States",
        authorization_reference="SECRET-INTERNAL-REF-123", notes="internal note",
    )
    resp = APIClient().get("/api/v1/legal/transfers/")
    assert resp.status_code == 200
    assert len(resp.json()["data"]) == 1
    row = resp.json()["data"][0]
    assert row["destination_country"] == "United States"
    assert row["processor_name"] == "Test Vendor"
    assert "authorization_reference" not in row
    assert "notes" not in row
    assert "SECRET-INTERNAL-REF-123" not in resp.content.decode()


def test_data_transfer_register_public_endpoint_reports_unknown_mechanism_honestly():
    """A transfer with no confirmed safeguard mechanism must show the
    honest 'unknown' state, never a silently-assumed default."""
    DataTransferRecord.objects.create(destination_country="Germany")
    resp = APIClient().get("/api/v1/legal/transfers/")
    row = resp.json()["data"][0]
    assert row["mechanism"] == "unknown"
