from unittest import mock
from mock import call

import pytest

from datetime import datetime, timedelta, timezone

# Tests for Secure class


def test_find_available_wallet(secure_class, mock_firestore):
    # Setup Firestore to return an available wallet
    wallet_mock = mock.MagicMock()
    wallet_mock.to_dict.return_value = {'is_rented': False}
    mock_firestore.collection.return_value.where.return_value.limit.return_value.stream.return_value = iter([
                                                                                                            wallet_mock])

    wallet = secure_class.find_available_wallet()

    assert wallet == wallet_mock
    mock_firestore.collection.assert_called_once_with('wallets')


def test_create_wallet(secure_class, mock_firestore):
    # Setup Firestore to create a wallet
    wallet_ref_mock = mock.MagicMock()
    wallet_ref_mock.id = 'wallet_uid'
    mock_firestore.collection.return_value.document.return_value = wallet_ref_mock

    wallet_uid, wallet_number = secure_class.create_wallet()

    assert wallet_uid is not None
    assert wallet_uid == 'wallet_uid'
    assert wallet_number == 1  # First wallet should have wallet number 1
    mock_firestore.collection.return_value.document.return_value.set.assert_called_once()


@pytest.mark.parametrize("user_uid, test_wallet_number", [
    ("test_uid1", 1),
    ("test_uid2", 5),
    ("test_uid3", 10),
    ("test_uid4", 100),
    ("test_uid5", 1000),
    ("test_uid6", 9999999999999),
    ("test_uid7", -1),
    ("test_uid8", -10),
    ("test_uid9", -463465434345),
    ("test_uid10", 2.5),
])
def test_rent_wallet_existing(user_uid, test_wallet_number, secure_class, mock_firestore, mock_unsecure):
    mock_wallet = mock.MagicMock()
    mock_wallet.to_dict.return_value = {
        'number': test_wallet_number, 'balance': 0, 'is_rented': False}
    mock_wallet.reference = mock.MagicMock()

    mock_firestore.collection.return_value.where.return_value.limit.return_value.stream.return_value = iter([
        mock_wallet])

    wallet_number = secure_class.rent_wallet(uid=user_uid)

    # Check that the wallet is rented and the unsecure project is linked
    assert wallet_number == test_wallet_number
    mock_wallet.reference.update.assert_called_with({
        'is_rented': True,
        'rental_expiry': mock.ANY  # We don't check exact value of expiry
    })
    mock_unsecure.link_wallet_to_user.assert_called_with(
        user_uid, test_wallet_number)


def test_rent_wallet_no_existing(secure_class, mock_firestore, mock_unsecure):
    mock_firestore.collection.return_value.where.return_value.limit.return_value.stream.return_value = iter([
    ])

    wallet_number = secure_class.rent_wallet(uid="user_456")

    # Since no wallet was available, a new one should be created
    assert wallet_number == 1  # The new wallet created should have number 1
    mock_unsecure.link_wallet_to_user.assert_called_with('user_456', 1)


def test_rent_wallet_user_not_exist(secure_class, mock_unsecure):
    """Test rent_wallet raises ValueError when the user does not exist."""

    # Mock the Firestore 'users' collection to return a non-existent user
    mock_unsecure.db.collection().document().get.return_value.exists = False

    # Define a non-existent user ID
    non_existent_uid = 'non_existent_user'

    # Attempt to rent a wallet for the non-existent user, should raise ValueError
    with pytest.raises(ValueError, match=f"User with UID {non_existent_uid} does not exist."):
        secure_class.rent_wallet(non_existent_uid)


@pytest.mark.parametrize("wallet_number, amount", [
    (1, 0),  # Zero
    (2, 1),  # one digit
    (3, 10),  # two digits
    (4, 100),  # three digits
    (5, 1000),  # four digits
    (6, 10000000000000),  # huges number
    (7, 4.5),  # float number
    (8, 5.3543545465)  # big float number
])
def test_deposit_to_wallet_within_rental_positive_amount(wallet_number, amount, secure_class, mock_unsecure, mock_firestore):
    mock_wallet = mock.MagicMock()
    start_balance = 100
    mock_wallet.to_dict.return_value = {
        'number': wallet_number,
        'balance': start_balance,
        'rental_expiry': datetime.now(timezone.utc) + timedelta(minutes=5),
        'is_rented': True
    }
    mock_wallet.reference = mock.MagicMock()

    mock_firestore.collection.return_value.where.return_value.limit.return_value.get.return_value = [
        mock_wallet]

    secure_class.deposit_to_wallet(wallet_number=wallet_number, amount=amount)

    # Check if wallet balance is updated
    new_balance = start_balance + amount
    mock_wallet.reference.update.assert_any_call({'balance': new_balance})

    # Check if the deposit was sent to the unsecure project
    mock_unsecure.update_user_balance.assert_called_with(wallet_number, amount)

    # Ensure the wallet is expired after the deposit
    mock_wallet.reference.update.assert_any_call({'is_rented': False})
    mock_unsecure.unlink_wallet_from_user.assert_called_with(wallet_number)


@pytest.mark.parametrize("amount", [
    (-1),  # negative with one digit
    (-10),  # negative with two digits
    (-100),  # negative with three digits
    (-1000),  # negative with four digits
    (-10000000000000),  # huge negative number
    (-2.5),  # negative float number
    (-6.453243543452)  # big negative float number
])
def test_deposit_to_wallet_within_rental_negative_amount(amount, secure_class, mock_unsecure, mock_firestore):
    # Setup wallet within rental period
    wallet_mock = mock.MagicMock()
    start_balance = 100
    wallet_mock.to_dict.return_value = {
        'number': 1,
        'balance': start_balance,
        'rental_expiry': datetime.now(timezone.utc) - timedelta(minutes=5),
        'is_rented': True
    }
    mock_firestore.collection.return_value.where.return_value.limit.return_value.get.return_value = [
        wallet_mock]

    secure_class.deposit_to_wallet(wallet_number=1, amount=amount)

    # Assert update was not called when the amount is negative
    mock_unsecure.reference.update.assert_not_called()


@pytest.mark.parametrize("amount", [
    (0),  # Zero
    (1),  # one digit
    (10),  # two digits
    (100),  # three digits
    (1000),  # four digits
    (10000000000000),  # huges number
    (4.5),  # float number
    (5.3543545465)  # big float number
])
def test_deposit_to_wallet_expired_positive_amount(amount, secure_class, mock_firestore, mock_unsecure):
    # Mock wallet document with expired rental period
    mock_wallet = mock.MagicMock()
    start_balance = 100
    mock_wallet.to_dict.return_value = {
        'number': 456,
        'balance': start_balance,
        'rental_expiry': datetime.now(timezone.utc) - timedelta(minutes=5),
        'is_rented': True
    }
    mock_wallet.reference = mock.MagicMock()

    mock_firestore.collection.return_value.where.return_value.limit.return_value.get.return_value = [
        mock_wallet]

    secure_class.deposit_to_wallet(wallet_number=456, amount=amount)

    # Check if wallet balance is updated but no unsecure updates are triggered
    new_balance = start_balance + amount
    mock_wallet.reference.update.assert_any_call({'balance': new_balance})
    mock_unsecure.update_user_balance.assert_not_called()
    mock_unsecure.unlink_wallet_from_user.assert_not_called()


@pytest.mark.parametrize("amount", [
    (-1),  # negative with one digit
    (-10),  # negative with two digits
    (-100),  # negative with three digits
    (-1000),  # negative with four digits
    (-10000000000000),  # huge negative number
    (-2.5),  # negative float number
    (-6.453243543452)  # big negative float number
])
def test_deposit_to_wallet_expired_negative_amount(amount, secure_class, mock_firestore, mock_unsecure):
    # Mock wallet document with expired rental period
    mock_wallet = mock.MagicMock()
    start_balance = 100
    mock_wallet.to_dict.return_value = {
        'number': 456,
        'balance': start_balance,
        'rental_expiry': datetime.now(timezone.utc) - timedelta(minutes=5),
        'is_rented': True
    }
    mock_wallet.reference = mock.MagicMock()

    mock_firestore.collection.return_value.where.return_value.limit.return_value.get.return_value = [
        mock_wallet]

    secure_class.deposit_to_wallet(wallet_number=456, amount=amount)

    # Assert update was not called when the amount is negative
    mock_unsecure.reference.update.assert_not_called()
