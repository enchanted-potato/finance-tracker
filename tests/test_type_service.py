import pytest

from app.models import AccountType, LiabilityType
from app.services.type_service import (
    account_type_usage_count,
    create_account_type,
    create_liability_type,
    delete_account_type,
    delete_liability_type,
    liability_type_usage_count,
    rename_account_type,
    rename_liability_type,
)


class TestCreateAccountType:
    def test_create_system_default(self, db_session):
        at = create_account_type(session=db_session, name="Real Estate")
        assert at.id is not None
        assert at.name == "Real Estate"
        assert at.user_id is None

    def test_create_user_custom(self, db_session, test_user):
        at = create_account_type(session=db_session, name="HSA", user_id=test_user.id)
        assert at.user_id == test_user.id


class TestRenameAccountType:
    def test_rename_success(self, db_session, account_type):
        renamed = rename_account_type(
            session=db_session, type_id=account_type.id, new_name="Current Account"
        )
        assert renamed.name == "Current Account"

    def test_rename_nonexistent(self, db_session):
        with pytest.raises(ValueError, match="not found"):
            rename_account_type(session=db_session, type_id=99999, new_name="Nope")


class TestDeleteAccountType:
    def test_delete_unused(self, db_session):
        at = AccountType(name="Temporary", user_id=None)
        db_session.add(at)
        db_session.flush()

        delete_account_type(session=db_session, type_id=at.id)
        assert db_session.get(AccountType, at.id) is None

    def test_delete_nonexistent(self, db_session):
        with pytest.raises(ValueError, match="not found"):
            delete_account_type(session=db_session, type_id=99999)

    def test_delete_in_use(self, db_session, make_account, account_type):
        make_account(name="My Savings")
        with pytest.raises(ValueError, match="accounts still reference it"):
            delete_account_type(session=db_session, type_id=account_type.id)


class TestAccountTypeUsageCount:
    def test_zero_when_unused(self, db_session, account_type):
        assert account_type_usage_count(session=db_session, type_id=account_type.id) == 0

    def test_counts_accounts(self, db_session, make_account, account_type):
        make_account(name="A1")
        make_account(name="A2")
        assert account_type_usage_count(session=db_session, type_id=account_type.id) == 2


class TestCreateLiabilityType:
    def test_create_system_default(self, db_session):
        lt = create_liability_type(session=db_session, name="Auto Loan")
        assert lt.id is not None
        assert lt.name == "Auto Loan"
        assert lt.user_id is None

    def test_create_user_custom(self, db_session, test_user):
        lt = create_liability_type(session=db_session, name="Tax Debt", user_id=test_user.id)
        assert lt.user_id == test_user.id


class TestRenameLiabilityType:
    def test_rename_success(self, db_session, liability_type):
        renamed = rename_liability_type(
            session=db_session, type_id=liability_type.id, new_name="Home Loan"
        )
        assert renamed.name == "Home Loan"

    def test_rename_nonexistent(self, db_session):
        with pytest.raises(ValueError, match="not found"):
            rename_liability_type(session=db_session, type_id=99999, new_name="Nope")


class TestDeleteLiabilityType:
    def test_delete_unused(self, db_session):
        lt = LiabilityType(name="Temporary", user_id=None)
        db_session.add(lt)
        db_session.flush()

        delete_liability_type(session=db_session, type_id=lt.id)
        assert db_session.get(LiabilityType, lt.id) is None

    def test_delete_nonexistent(self, db_session):
        with pytest.raises(ValueError, match="not found"):
            delete_liability_type(session=db_session, type_id=99999)

    def test_delete_in_use(self, db_session, make_liability, liability_type):
        make_liability(name="My Mortgage")
        with pytest.raises(ValueError, match="liabilities still reference it"):
            delete_liability_type(session=db_session, type_id=liability_type.id)


class TestLiabilityTypeUsageCount:
    def test_zero_when_unused(self, db_session, liability_type):
        assert liability_type_usage_count(session=db_session, type_id=liability_type.id) == 0

    def test_counts_liabilities(self, db_session, make_liability, liability_type):
        make_liability(name="L1")
        make_liability(name="L2")
        assert liability_type_usage_count(session=db_session, type_id=liability_type.id) == 2
