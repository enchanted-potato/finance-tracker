from decimal import Decimal

import pytest

from app.services.liability_service import (
    create_liability,
    deactivate_liability,
    get_liability,
    list_liabilities,
    list_liability_types,
    update_balance,
)


class TestCreateLiability:
    def test_create_liability_basic(self, db_session, test_user, liability_type):
        liability = create_liability(
            session=db_session,
            user_id=test_user.id,
            liability_type_id=liability_type.id,
            name="Home Mortgage",
            balance=Decimal("250000"),
        )
        assert liability.id is not None
        assert liability.name == "Home Mortgage"
        assert liability.balance == Decimal("250000")
        assert liability.currency == "GBP"
        assert liability.is_active is True

    def test_create_liability_default_balance(self, db_session, test_user, liability_type):
        liability = create_liability(
            session=db_session,
            user_id=test_user.id,
            liability_type_id=liability_type.id,
            name="New Loan",
        )
        assert liability.balance == Decimal("0")


class TestListLiabilities:
    def test_list_liabilities_empty(self, db_session, test_user):
        liabilities = list_liabilities(session=db_session, user_id=test_user.id)
        assert liabilities == []

    def test_list_liabilities_returns_active(self, db_session, test_user, make_liability):
        make_liability(name="Mortgage")
        make_liability(name="Auto Loan")
        liabilities = list_liabilities(session=db_session, user_id=test_user.id)
        assert len(liabilities) == 2

    def test_list_liabilities_excludes_inactive(self, db_session, test_user, make_liability):
        make_liability(name="Active")
        inactive = make_liability(name="Paid Off")
        inactive.is_active = False
        db_session.flush()

        liabilities = list_liabilities(session=db_session, user_id=test_user.id, active_only=True)
        assert len(liabilities) == 1
        assert liabilities[0].name == "Active"

    def test_list_liabilities_includes_inactive(self, db_session, test_user, make_liability):
        make_liability(name="Active")
        inactive = make_liability(name="Paid Off")
        inactive.is_active = False
        db_session.flush()

        liabilities = list_liabilities(session=db_session, user_id=test_user.id, active_only=False)
        assert len(liabilities) == 2

    def test_list_liabilities_scoped_to_user(self, db_session, test_user, liability_type):
        from app.models import User

        other_user = User(id="other-user-2", email="other2@example.com")
        db_session.add(other_user)
        db_session.flush()

        create_liability(
            session=db_session,
            user_id=test_user.id,
            liability_type_id=liability_type.id,
            name="My Mortgage",
        )
        create_liability(
            session=db_session,
            user_id=other_user.id,
            liability_type_id=liability_type.id,
            name="Their Mortgage",
        )

        my_liabilities = list_liabilities(session=db_session, user_id=test_user.id)
        assert len(my_liabilities) == 1
        assert my_liabilities[0].name == "My Mortgage"


class TestGetLiability:
    def test_get_existing_liability(self, db_session, test_user, make_liability):
        created = make_liability(name="Mortgage")
        fetched = get_liability(session=db_session, liability_id=created.id, user_id=test_user.id)
        assert fetched is not None
        assert fetched.id == created.id

    def test_get_nonexistent_liability(self, db_session, test_user):
        fetched = get_liability(session=db_session, liability_id=99999, user_id=test_user.id)
        assert fetched is None

    def test_get_liability_wrong_user(self, db_session, make_liability):
        created = make_liability(name="Mortgage")
        fetched = get_liability(session=db_session, liability_id=created.id, user_id="wrong-user")
        assert fetched is None


class TestUpdateBalance:
    def test_update_balance_success(self, db_session, test_user, make_liability):
        liability = make_liability(name="Mortgage", balance=Decimal("200000"))
        updated = update_balance(
            session=db_session,
            liability_id=liability.id,
            user_id=test_user.id,
            new_balance=Decimal("195000"),
        )
        assert updated.balance == Decimal("195000")

    def test_update_balance_nonexistent(self, db_session, test_user):
        with pytest.raises(ValueError, match="not found"):
            update_balance(
                session=db_session,
                liability_id=99999,
                user_id=test_user.id,
                new_balance=Decimal("100"),
            )

    def test_update_balance_inactive_liability(self, db_session, test_user, make_liability):
        liability = make_liability(name="Paid Off Loan")
        liability.is_active = False
        db_session.flush()

        with pytest.raises(ValueError, match="deactivated"):
            update_balance(
                session=db_session,
                liability_id=liability.id,
                user_id=test_user.id,
                new_balance=Decimal("100"),
            )


class TestDeactivateLiability:
    def test_deactivate_success(self, db_session, test_user, make_liability):
        liability = make_liability(name="To Deactivate")
        deactivated = deactivate_liability(
            session=db_session, liability_id=liability.id, user_id=test_user.id
        )
        assert deactivated.is_active is False

    def test_deactivate_nonexistent(self, db_session, test_user):
        with pytest.raises(ValueError, match="not found"):
            deactivate_liability(session=db_session, liability_id=99999, user_id=test_user.id)


class TestListLiabilityTypes:
    def test_list_includes_system_defaults(self, db_session, test_user, liability_type):
        types = list_liability_types(session=db_session, user_id=test_user.id)
        assert any(t.name == "Mortgage" for t in types)

    def test_list_includes_user_custom(self, db_session, test_user, liability_type):
        from app.models import LiabilityType

        custom = LiabilityType(name="Tax Debt", user_id=test_user.id)
        db_session.add(custom)
        db_session.flush()

        types = list_liability_types(session=db_session, user_id=test_user.id)
        names = {t.name for t in types}
        assert "Mortgage" in names
        assert "Tax Debt" in names
