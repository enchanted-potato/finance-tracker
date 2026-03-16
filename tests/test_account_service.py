from datetime import date
from decimal import Decimal

import pytest

from app.models import AccountType
from app.services.account_service import (
    delete_account_entry,
    list_account_entries,
    list_account_types,
    list_non_pension_entries,
    list_pension_entries,
    upsert_account_entry,
)


class TestUpsertAccountEntry:
    def test_create_new_entry(self, db_session, test_user, account_type):
        entry = upsert_account_entry(
            session=db_session,
            user_id=test_user.id,
            account_type_id=account_type.id,
            entry_date=date(2025, 1, 1),
            balance=Decimal("5000"),
        )
        assert entry.id is not None
        assert entry.balance == Decimal("5000")
        assert entry.entry_date == date(2025, 1, 1)
        assert entry.account_type_id == account_type.id

    def test_upsert_updates_existing(self, db_session, test_user, account_type):
        entry1 = upsert_account_entry(
            session=db_session,
            user_id=test_user.id,
            account_type_id=account_type.id,
            entry_date=date(2025, 1, 1),
            balance=Decimal("1000"),
        )
        entry2 = upsert_account_entry(
            session=db_session,
            user_id=test_user.id,
            account_type_id=account_type.id,
            entry_date=date(2025, 1, 1),
            balance=Decimal("2500"),
        )
        assert entry2.id == entry1.id
        assert entry2.balance == Decimal("2500")

    def test_upsert_default_balance(self, db_session, test_user, account_type):
        entry = upsert_account_entry(
            session=db_session,
            user_id=test_user.id,
            account_type_id=account_type.id,
            entry_date=date(2025, 2, 1),
        )
        assert entry.balance == Decimal("0")

    def test_different_dates_create_separate_entries(self, db_session, test_user, account_type):
        upsert_account_entry(
            session=db_session,
            user_id=test_user.id,
            account_type_id=account_type.id,
            entry_date=date(2025, 1, 1),
            balance=Decimal("1000"),
        )
        upsert_account_entry(
            session=db_session,
            user_id=test_user.id,
            account_type_id=account_type.id,
            entry_date=date(2025, 2, 1),
            balance=Decimal("2000"),
        )
        entries = list_account_entries(session=db_session, user_id=test_user.id)
        assert len(entries) == 2


class TestDeleteAccountEntry:
    def test_delete_success(self, db_session, test_user, account_type):
        entry = upsert_account_entry(
            session=db_session,
            user_id=test_user.id,
            account_type_id=account_type.id,
            entry_date=date(2025, 1, 1),
            balance=Decimal("500"),
        )
        affected_date = delete_account_entry(
            session=db_session, entry_id=entry.id, user_id=test_user.id
        )
        assert affected_date == date(2025, 1, 1)
        entries = list_account_entries(session=db_session, user_id=test_user.id)
        assert entries == []

    def test_delete_nonexistent_raises(self, db_session, test_user):
        with pytest.raises(ValueError, match="not found"):
            delete_account_entry(session=db_session, entry_id=99999, user_id=test_user.id)

    def test_delete_wrong_user_raises(self, db_session, test_user, account_type):
        entry = upsert_account_entry(
            session=db_session,
            user_id=test_user.id,
            account_type_id=account_type.id,
            entry_date=date(2025, 1, 1),
            balance=Decimal("500"),
        )
        with pytest.raises(ValueError, match="not found"):
            delete_account_entry(
                session=db_session, entry_id=entry.id, user_id="wrong-user"
            )


class TestListAccountEntries:
    def test_list_empty(self, db_session, test_user):
        entries = list_account_entries(session=db_session, user_id=test_user.id)
        assert entries == []

    def test_list_ordered_newest_first(self, db_session, test_user, account_type):
        upsert_account_entry(
            session=db_session,
            user_id=test_user.id,
            account_type_id=account_type.id,
            entry_date=date(2025, 1, 1),
            balance=Decimal("1000"),
        )
        upsert_account_entry(
            session=db_session,
            user_id=test_user.id,
            account_type_id=account_type.id,
            entry_date=date(2025, 3, 1),
            balance=Decimal("3000"),
        )
        entries = list_account_entries(session=db_session, user_id=test_user.id)
        assert entries[0].entry_date > entries[1].entry_date

    def test_list_scoped_to_user(self, db_session, test_user, account_type):
        upsert_account_entry(
            session=db_session,
            user_id=test_user.id,
            account_type_id=account_type.id,
            entry_date=date(2025, 1, 1),
            balance=Decimal("1000"),
        )
        upsert_account_entry(
            session=db_session,
            user_id="other-user",
            account_type_id=account_type.id,
            entry_date=date(2025, 1, 1),
            balance=Decimal("9999"),
        )
        entries = list_account_entries(session=db_session, user_id=test_user.id)
        assert len(entries) == 1
        assert all(e.user_id == test_user.id for e in entries)


class TestListPensionEntries:
    def test_returns_only_pension(self, db_session, test_user, account_type):
        """Pension entries are returned; non-pension entries are excluded."""
        pension_type = AccountType(name="Pension", user_id=None)
        db_session.add(pension_type)
        db_session.flush()

        upsert_account_entry(
            session=db_session,
            user_id=test_user.id,
            account_type_id=pension_type.id,
            entry_date=date(2025, 1, 1),
            balance=Decimal("50000"),
        )
        upsert_account_entry(
            session=db_session,
            user_id=test_user.id,
            account_type_id=account_type.id,
            entry_date=date(2025, 1, 1),
            balance=Decimal("10000"),
        )

        pension = list_pension_entries(session=db_session, user_id=test_user.id)
        non_pension = list_non_pension_entries(session=db_session, user_id=test_user.id)

        assert len(pension) == 1
        assert pension[0].account_type_id == pension_type.id
        assert len(non_pension) == 1
        assert non_pension[0].account_type_id == account_type.id


class TestListAccountTypes:
    def test_list_includes_system_defaults(self, db_session, test_user, account_type):
        types = list_account_types(session=db_session, user_id=test_user.id)
        assert any(t.name == "Checking" for t in types)

    def test_list_includes_user_custom(self, db_session, test_user, account_type):
        custom = AccountType(name="HSA", user_id=test_user.id)
        db_session.add(custom)
        db_session.flush()

        types = list_account_types(session=db_session, user_id=test_user.id)
        names = {t.name for t in types}
        assert "Checking" in names
        assert "HSA" in names
