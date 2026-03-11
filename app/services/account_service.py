from decimal import Decimal

from loguru import logger
from sqlmodel import Session, select

from app.models import Account, AccountType

PENSION_TYPE_NAME = "Pension"


def _get_pension_type_id(session: Session, user_id: str) -> int | None:
    """Return the AccountType.id for 'Pension' visible to this user, or None.

    :param session: Database session.
    :param user_id: Firebase UID of the owner.
    :returns: The id of the Pension account type, or None if not found.
    """
    statement = select(AccountType).where(
        (AccountType.name == PENSION_TYPE_NAME),
        (AccountType.user_id.is_(None)) | (AccountType.user_id == user_id),
    )
    at = session.exec(statement).first()
    return at.id if at else None


def list_pension_accounts(*, session: Session, user_id: str, active_only: bool = True) -> list[Account]:
    """List accounts whose type is 'Pension'.

    :param session: Database session.
    :param user_id: Firebase UID of the owner.
    :param active_only: If True, exclude deactivated accounts.
    :returns: List of pension accounts ordered by name.
    """
    pension_type_id = _get_pension_type_id(session, user_id)
    if pension_type_id is None:
        return []
    statement = select(Account).where(
        Account.user_id == user_id,
        Account.account_type_id == pension_type_id,
    )
    if active_only:
        statement = statement.where(Account.is_active.is_(True))
    statement = statement.order_by(Account.name)
    return list(session.exec(statement).all())


def list_non_pension_accounts(*, session: Session, user_id: str, active_only: bool = True) -> list[Account]:
    """List accounts whose type is NOT 'Pension' (used for Total Assets).

    :param session: Database session.
    :param user_id: Firebase UID of the owner.
    :param active_only: If True, exclude deactivated accounts.
    :returns: List of non-pension accounts ordered by type and name.
    """
    pension_type_id = _get_pension_type_id(session, user_id)
    statement = select(Account).where(Account.user_id == user_id)
    if pension_type_id is not None:
        statement = statement.where(Account.account_type_id != pension_type_id)
    if active_only:
        statement = statement.where(Account.is_active.is_(True))
    statement = statement.order_by(Account.account_type_id, Account.name)
    return list(session.exec(statement).all())


def create_account(
    *,
    session: Session,
    user_id: str,
    account_type_id: int,
    name: str,
    balance: Decimal = Decimal("0"),
    currency: str = "GBP",
    exchange_rate: Decimal = Decimal("1"),
) -> Account:
    """Create a new asset account.

    :param session: Database session.
    :param user_id: Firebase UID of the owner.
    :param account_type_id: FK to account_types.
    :param name: Display name for the account.
    :param balance: Initial balance in native currency.
    :param currency: ISO 4217 currency code.
    :param exchange_rate: Exchange rate to GBP (balance_gbp = balance * exchange_rate).
    :returns: The newly created account.
    """
    account = Account(
        user_id=user_id,
        account_type_id=account_type_id,
        name=name,
        balance=balance,
        currency=currency,
        exchange_rate=exchange_rate,
    )
    session.add(account)
    session.commit()
    session.refresh(account)
    logger.info(f"Created account '{name}' (id={account.id}) for user {user_id}")
    return account


def list_accounts(*, session: Session, user_id: str, active_only: bool = True) -> list[Account]:
    """List accounts for a user.

    :param session: Database session.
    :param user_id: Firebase UID of the owner.
    :param active_only: If True, exclude deactivated accounts.
    :returns: List of accounts.
    """
    statement = select(Account).where(Account.user_id == user_id)
    if active_only:
        statement = statement.where(Account.is_active.is_(True))
    statement = statement.order_by(Account.account_type_id, Account.name)
    return list(session.exec(statement).all())


def get_account(*, session: Session, account_id: int, user_id: str) -> Account | None:
    """Fetch a single account by ID.

    :param session: Database session.
    :param account_id: Primary key of the account.
    :param user_id: Firebase UID of the owner.
    :returns: The account or None if not found.
    """
    statement = select(Account).where(Account.id == account_id, Account.user_id == user_id)
    return session.exec(statement).first()


def update_balance(
    *,
    session: Session,
    account_id: int,
    user_id: str,
    new_balance: Decimal,
) -> Account:
    """Update the balance of an account.

    :param session: Database session.
    :param account_id: Primary key of the account.
    :param user_id: Firebase UID of the owner.
    :param new_balance: The new balance value.
    :returns: The updated account.
    :raises ValueError: If the account is not found or inactive.
    """
    account = get_account(session=session, account_id=account_id, user_id=user_id)
    if account is None:
        raise ValueError(f"Account {account_id} not found for user {user_id}")
    if not account.is_active:
        raise ValueError(f"Account {account_id} is deactivated")
    account.balance = new_balance
    session.add(account)
    session.commit()
    session.refresh(account)
    logger.info(f"Updated account {account_id} balance to {new_balance}")
    return account


def update_account(
    *,
    session: Session,
    account_id: int,
    user_id: str,
    name: str | None = None,
    balance: Decimal | None = None,
    currency: str | None = None,
    exchange_rate: Decimal | None = None,
) -> Account:
    """Update an account's name, balance, currency, and/or exchange rate.

    :param session: Database session.
    :param account_id: Primary key of the account.
    :param user_id: Firebase UID of the owner.
    :param name: New display name, or None to leave unchanged.
    :param balance: New balance in native currency, or None to leave unchanged.
    :param currency: New ISO 4217 currency code, or None to leave unchanged.
    :param exchange_rate: New exchange rate to GBP, or None to leave unchanged.
    :returns: The updated account.
    :raises ValueError: If the account is not found or inactive.
    """
    account = get_account(session=session, account_id=account_id, user_id=user_id)
    if account is None:
        raise ValueError(f"Account {account_id} not found for user {user_id}")
    if not account.is_active:
        raise ValueError(f"Account {account_id} is deactivated")
    if name is not None:
        account.name = name
    if balance is not None:
        account.balance = balance
    if currency is not None:
        account.currency = currency
    if exchange_rate is not None:
        account.exchange_rate = exchange_rate
    session.add(account)
    session.commit()
    session.refresh(account)
    logger.info(f"Updated account {account_id}")
    return account


def deactivate_account(*, session: Session, account_id: int, user_id: str) -> Account:
    """Soft-delete an account by marking it inactive.

    :param session: Database session.
    :param account_id: Primary key of the account.
    :param user_id: Firebase UID of the owner.
    :returns: The deactivated account.
    :raises ValueError: If the account is not found.
    """
    account = get_account(session=session, account_id=account_id, user_id=user_id)
    if account is None:
        raise ValueError(f"Account {account_id} not found for user {user_id}")
    account.is_active = False
    session.add(account)
    session.commit()
    session.refresh(account)
    logger.info(f"Deactivated account {account_id}")
    return account


def list_account_types(*, session: Session, user_id: str) -> list[AccountType]:
    """List account types visible to a user (system defaults + user custom).

    :param session: Database session.
    :param user_id: Firebase UID of the owner.
    :returns: List of account types.
    """
    statement = select(AccountType).where(
        (AccountType.user_id.is_(None)) | (AccountType.user_id == user_id)
    )
    return list(session.exec(statement.order_by(AccountType.name)).all())
