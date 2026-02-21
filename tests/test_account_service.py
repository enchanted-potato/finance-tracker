from decimal import Decimal

import pytest

from app.services.account_service import (
    create_account,
    deactivate_account,
    get_account,
    list_account_types,
    list_accounts,
    update_balance,
)


class TestCreateAccount:
    def test_create_account_basic(self, db_session, test_user, account_type):
        account = create_account(
            session=db_session,
            user_id=test_user.id,
            account_type_id=account_type.id,
            name="Chase Checking",
            balance=Decimal("5000"),
        )
        assert account.id is not None
        assert account.name == "Chase Checking"
        assert account.balance == Decimal("5000")
        assert account.currency == "GBP"
        assert account.is_active is True

    def test_create_account_default_balance(self, db_session, test_user, account_type):
        account = create_account(
            session=db_session,
            user_id=test_user.id,
            account_type_id=account_type.id,
            name="Empty Account",
        )
        assert account.balance == Decimal("0")

    def test_create_account_custom_currency(self, db_session, test_user, account_type):
        account = create_account(
            session=db_session,
            user_id=test_user.id,
            account_type_id=account_type.id,
            name="Euro Account",
            balance=Decimal("1000"),
            currency="EUR",
        )
        assert account.currency == "EUR"


class TestListAccounts:
    def test_list_accounts_empty(self, db_session, test_user):
        accounts = list_accounts(session=db_session, user_id=test_user.id)
        assert accounts == []

    def test_list_accounts_returns_active(self, db_session, test_user, make_account):
        make_account(name="Account 1")
        make_account(name="Account 2")
        accounts = list_accounts(session=db_session, user_id=test_user.id)
        assert len(accounts) == 2

    def test_list_accounts_excludes_inactive(self, db_session, test_user, make_account):
        make_account(name="Active")
        inactive = make_account(name="Inactive")
        inactive.is_active = False
        db_session.flush()

        accounts = list_accounts(session=db_session, user_id=test_user.id, active_only=True)
        assert len(accounts) == 1
        assert accounts[0].name == "Active"

    def test_list_accounts_includes_inactive(self, db_session, test_user, make_account):
        make_account(name="Active")
        inactive = make_account(name="Inactive")
        inactive.is_active = False
        db_session.flush()

        accounts = list_accounts(session=db_session, user_id=test_user.id, active_only=False)
        assert len(accounts) == 2

    def test_list_accounts_scoped_to_user(self, db_session, test_user, account_type):
        from app.models import User

        other_user = User(id="other-user", email="other@example.com")
        db_session.add(other_user)
        db_session.flush()

        create_account(
            session=db_session,
            user_id=test_user.id,
            account_type_id=account_type.id,
            name="My Account",
        )
        create_account(
            session=db_session,
            user_id=other_user.id,
            account_type_id=account_type.id,
            name="Other Account",
        )

        my_accounts = list_accounts(session=db_session, user_id=test_user.id)
        assert len(my_accounts) == 1
        assert my_accounts[0].name == "My Account"


class TestGetAccount:
    def test_get_existing_account(self, db_session, test_user, make_account):
        created = make_account(name="Savings")
        fetched = get_account(session=db_session, account_id=created.id, user_id=test_user.id)
        assert fetched is not None
        assert fetched.id == created.id

    def test_get_nonexistent_account(self, db_session, test_user):
        fetched = get_account(session=db_session, account_id=99999, user_id=test_user.id)
        assert fetched is None

    def test_get_account_wrong_user(self, db_session, make_account):
        created = make_account(name="Savings")
        fetched = get_account(session=db_session, account_id=created.id, user_id="wrong-user")
        assert fetched is None


class TestUpdateBalance:
    def test_update_balance_success(self, db_session, test_user, make_account):
        account = make_account(name="Checking", balance=Decimal("1000"))
        updated = update_balance(
            session=db_session,
            account_id=account.id,
            user_id=test_user.id,
            new_balance=Decimal("2500"),
        )
        assert updated.balance == Decimal("2500")

    def test_update_balance_nonexistent(self, db_session, test_user):
        with pytest.raises(ValueError, match="not found"):
            update_balance(
                session=db_session,
                account_id=99999,
                user_id=test_user.id,
                new_balance=Decimal("100"),
            )

    def test_update_balance_inactive_account(self, db_session, test_user, make_account):
        account = make_account(name="Old Account")
        account.is_active = False
        db_session.flush()

        with pytest.raises(ValueError, match="deactivated"):
            update_balance(
                session=db_session,
                account_id=account.id,
                user_id=test_user.id,
                new_balance=Decimal("100"),
            )


class TestDeactivateAccount:
    def test_deactivate_success(self, db_session, test_user, make_account):
        account = make_account(name="To Deactivate")
        deactivated = deactivate_account(
            session=db_session, account_id=account.id, user_id=test_user.id
        )
        assert deactivated.is_active is False

    def test_deactivate_nonexistent(self, db_session, test_user):
        with pytest.raises(ValueError, match="not found"):
            deactivate_account(session=db_session, account_id=99999, user_id=test_user.id)


class TestListAccountTypes:
    def test_list_includes_system_defaults(self, db_session, test_user, account_type):
        types = list_account_types(session=db_session, user_id=test_user.id)
        assert any(t.name == "Checking" for t in types)

    def test_list_includes_user_custom(self, db_session, test_user, account_type):
        from app.models import AccountType

        custom = AccountType(name="HSA", user_id=test_user.id)
        db_session.add(custom)
        db_session.flush()

        types = list_account_types(session=db_session, user_id=test_user.id)
        names = {t.name for t in types}
        assert "Checking" in names
        assert "HSA" in names
