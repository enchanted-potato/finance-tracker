from datetime import date
from decimal import Decimal

import pytest

from app.services.liability_service import (
    delete_liability_entry,
    list_liability_entries,
    list_liability_types,
    upsert_liability_entry,
)


class TestUpsertLiabilityEntry:
    def test_create_new_entry(self, db_session, test_user, liability_type):
        entry = upsert_liability_entry(
            session=db_session,
            user_id=test_user.id,
            liability_type_id=liability_type.id,
            entry_date=date(2026, 3, 1),
            amount=Decimal("200000"),
        )
        assert entry.id is not None
        assert entry.amount == Decimal("200000")
        assert entry.currency == "GBP"

    def test_upsert_updates_existing(self, db_session, test_user, liability_type):
        d = date(2026, 3, 1)
        upsert_liability_entry(
            session=db_session,
            user_id=test_user.id,
            liability_type_id=liability_type.id,
            entry_date=d,
            amount=Decimal("200000"),
        )
        updated = upsert_liability_entry(
            session=db_session,
            user_id=test_user.id,
            liability_type_id=liability_type.id,
            entry_date=d,
            amount=Decimal("195000"),
        )
        assert updated.amount == Decimal("195000")
        all_entries = list_liability_entries(session=db_session, user_id=test_user.id)
        assert len(all_entries) == 1


class TestDeleteLiabilityEntry:
    def test_delete_success(self, db_session, test_user, make_liability):
        entry = make_liability(amount=Decimal("100000"))
        affected_date = delete_liability_entry(
            session=db_session, entry_id=entry.id, user_id=test_user.id
        )
        assert affected_date == entry.entry_date
        assert list_liability_entries(session=db_session, user_id=test_user.id) == []

    def test_delete_nonexistent(self, db_session, test_user):
        with pytest.raises(ValueError, match="not found"):
            delete_liability_entry(session=db_session, entry_id=99999, user_id=test_user.id)

    def test_delete_wrong_user(self, db_session, make_liability):
        entry = make_liability()
        with pytest.raises(ValueError, match="not found"):
            delete_liability_entry(session=db_session, entry_id=entry.id, user_id="wrong-user")


class TestListLiabilityEntries:
    def test_empty(self, db_session, test_user):
        assert list_liability_entries(session=db_session, user_id=test_user.id) == []

    def test_returns_entries(self, db_session, test_user, make_liability):
        make_liability(entry_date=date(2026, 1, 1))
        make_liability(entry_date=date(2026, 2, 1))
        entries = list_liability_entries(session=db_session, user_id=test_user.id)
        assert len(entries) == 2

    def test_ordered_newest_first(self, db_session, test_user, make_liability):
        make_liability(entry_date=date(2026, 1, 1))
        make_liability(entry_date=date(2026, 3, 1))
        entries = list_liability_entries(session=db_session, user_id=test_user.id)
        assert entries[0].entry_date > entries[1].entry_date

    def test_scoped_to_user(self, db_session, test_user, liability_type, make_liability):
        make_liability()
        upsert_liability_entry(
            session=db_session,
            user_id="other-user",
            liability_type_id=liability_type.id,
            entry_date=date(2026, 3, 1),
            amount=Decimal("50000"),
        )
        entries = list_liability_entries(session=db_session, user_id=test_user.id)
        assert len(entries) == 1


class TestListLiabilityTypes:
    def test_includes_system_defaults(self, db_session, test_user, liability_type):
        types = list_liability_types(session=db_session, user_id=test_user.id)
        assert any(t.name == "Mortgage" for t in types)

    def test_includes_user_custom(self, db_session, test_user, liability_type):
        from app.models import LiabilityType

        custom = LiabilityType(name="Tax Debt", user_id=test_user.id)
        db_session.add(custom)
        db_session.flush()

        types = list_liability_types(session=db_session, user_id=test_user.id)
        names = {t.name for t in types}
        assert "Mortgage" in names
        assert "Tax Debt" in names
