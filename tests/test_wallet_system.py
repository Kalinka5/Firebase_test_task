from unittest import mock
from mock import call

import pytest

from firebase_admin import firestore

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

    assert wallet_uid == 'wallet_uid'
    assert wallet_number == 1
    mock_firestore.collection.return_value.document.return_value.set.assert_called_once()


@pytest.mark.parametrize("user_uid, wallet_number_t, wallet_number_m", [
    ("test_uid1", 1, 1),
    ("test_uid2", 2, 2),
    ("test_uid3", 3, 3),
    ("test_uid4", 4, 4),
    ("test_uid5", 5, 5),
])
def test_rent_wallet_available_wallet(user_uid, wallet_number_t, wallet_number_m, secure_class, mock_unsecure, mock_firestore):
    # Setup an available wallet
    wallet_mock = mock.MagicMock()
    wallet_mock.to_dict.return_value = {
        'is_rented': False, 'number': wallet_number_m}
    mock_firestore.collection.return_value.where.return_value.limit.return_value.stream.return_value = iter([
        wallet_mock])

    wallet_number = secure_class.rent_wallet(uid=user_uid)

    assert wallet_number == wallet_number_t
    mock_unsecure.link_wallet_to_user.assert_called_once_with(
        user_uid, wallet_number_t)


def test_rent_wallet_no_available_wallet(secure_class, mock_unsecure, mock_firestore):
    # No available wallet, so create one
    mock_firestore.collection.return_value.where.return_value.limit.return_value.stream.return_value = iter([
    ])
    wallet_ref_mock = mock.MagicMock()
    wallet_ref_mock.id = 'wallet_uid'
    mock_firestore.collection.return_value.document.return_value = wallet_ref_mock

    wallet_number = secure_class.rent_wallet(uid='test_uid')

    assert wallet_number == 1
    mock_unsecure.link_wallet_to_user.assert_called_once_with('test_uid', 1)


@pytest.mark.parametrize("amount", [
    (0),  # Zero
    (1),  # one digit
    (10),  # two digits
    (100),  # three digits
    (1000),  # four digits
    (10000000000000),  # huges number
])
def test_deposit_to_wallet_within_rental_positive_amount(amount, secure_class, mock_unsecure, mock_firestore):
    # Setup wallet within rental period
    wallet_mock = mock.MagicMock()
    start_balance = 100
    wallet_mock.to_dict.return_value = {
        'balance': start_balance,
        'number': 1,
        'rental_expiry': datetime.now(timezone.utc) + timedelta(minutes=5)
    }
    mock_firestore.collection.return_value.where.return_value.limit.return_value.get.return_value = [
        wallet_mock]

    secure_class.deposit_to_wallet(wallet_number=1, amount=amount)

    # Verify Firestore and unsecure project interactions
    new_balance = start_balance + amount
    wallet_mock.reference.update.assert_has_calls(
        [call({'balance': new_balance}), call({'is_rented': False})])
    mock_unsecure.update_user_balance.assert_called_once_with(1, amount)


@pytest.mark.parametrize("amount", [
    (-1),  # negative with one digit
    (-10),  # negative with two digits
    (-100),  # negative with three digits
    (-1000),  # negative with four digits
    (-10000000000000),  # huge negative number
])
def test_deposit_to_wallet_within_rental_negative_amount(amount, secure_class, mock_unsecure, mock_firestore):
    # Setup wallet within rental period
    wallet_mock = mock.MagicMock()
    start_balance = 100
    wallet_mock.to_dict.return_value = {
        'balance': start_balance,
        'number': 1,
        'rental_expiry': datetime.now(timezone.utc) + timedelta(minutes=5)
    }
    mock_firestore.collection.return_value.where.return_value.limit.return_value.get.return_value = [
        wallet_mock]

    secure_class.deposit_to_wallet(wallet_number=1, amount=amount)

    # Assert update was not called when the amount is negative
    mock_unsecure.reference.update.assert_not_called()


def test_deposit_to_wallet_expired_rental(secure_class, mock_unsecure, mock_firestore):
    # Setup wallet with expired rental period
    wallet_mock = mock.MagicMock()
    wallet_mock.to_dict.return_value = {
        'balance': 100,
        'number': 1,
        'rental_expiry': datetime.now(timezone.utc) - timedelta(minutes=5)
    }
    mock_firestore.collection.return_value.where.return_value.limit.return_value.get.return_value = [
        wallet_mock]

    secure_class.deposit_to_wallet(wallet_number=1, amount=50)

    # Verify Firestore and unsecure project interactions
    wallet_mock.reference.update.assert_called_once_with({'balance': 150})
    mock_unsecure.update_user_balance.assert_not_called()


# Tests for Unsecure class

@pytest.mark.parametrize("user_uid", [
    ("1"),  # string with only number
    ("45656547678456"),  # string with only numbers
    (0),  # integer
    (45654466873),  # big integer
    (2.5),  # float number
    (0.45465443545),  # big float number
    (-1),  # negative number
    (-435646234354543),  # huge negative number
    (""),  # empty string
    ("test_uid"),  # string with letters
    ("test_uid344546")  # string with letters and numbers
])
def test_register_user(user_uid, unsecure_class, mock_firestore):
    """Test register_user for Unsecure class with different data types."""
    user_ref_mock = mock.MagicMock()
    mock_firestore.collection.return_value.document.return_value = user_ref_mock

    unsecure_class.register_user(uid=user_uid)

    user_ref_mock.set.assert_called_once_with(
        {'uid': user_uid, 'balance': 0})


@pytest.mark.parametrize("wallet_number", [
    (0),  # zero
    (1),  # one digit
    (-2),  # negative number
    (-1000000000),  # huge negative number
    (5),  # 5
    (10),  # two digits
    (999),  # three digits
    (9999999999999)  # huge positive number
])
def test_link_wallet_to_user(wallet_number, unsecure_class, mock_firestore):
    """Test link_wallet_to_user for Unsecure class with positive and negative numbers."""

    user_ref_mock = mock.MagicMock()
    mock_firestore.collection.return_value.document.return_value = user_ref_mock

    unsecure_class.link_wallet_to_user(
        uid='test_uid', wallet_number=wallet_number)

    user_ref_mock.update.assert_called_once_with(
        {'rented_wallet': wallet_number})


@pytest.mark.parametrize("wallet_number", [
    (0),  # zero
    (1),  # one digit
    (-2),  # negative number
    (-1000000000),  # huge negative number
    (5),  # 5
    (10),  # two digits
    (999),  # three digits
    (9999999999999)  # huge positive number
])
def test_unlink_wallet_from_user(wallet_number, unsecure_class, mock_firestore):
    """Test unlink_wallet_from_user for Unsecure class with positive and negative numbers."""

    # Mock the user reference and the returned document from Firestore
    user_mock = mock.MagicMock()
    mock_firestore.collection.return_value.where.return_value.limit.return_value.get.return_value = [
        user_mock]

    # Call the method with a test wallet number
    unsecure_class.unlink_wallet_from_user(wallet_number=wallet_number)

    # Ensure that the rented_wallet field is deleted
    user_mock.reference.update.assert_called_once_with(
        {'rented_wallet': firestore.DELETE_FIELD})


@pytest.mark.parametrize("amount", [
    (0),  # Zero
    (1),  # one digit
    (10),  # two digits
    (100),  # three digits
    (1000),  # four digits
    (10000000000000),  # huges number
])
def test_update_user_balance_positive_amount(unsecure_class, mock_firestore, amount):
    """Test update_user_balance for Unsecure class with positive amounts."""

    # Mock user document
    user_mock = mock.MagicMock()
    start_balance = 100
    user_mock.to_dict.return_value = {'balance': start_balance}
    mock_firestore.collection.return_value.where.return_value.limit.return_value.get.return_value = [
        user_mock]

    # Call the method with test wallet_number and amount
    wallet_number = 1
    unsecure_class.update_user_balance(wallet_number, amount)

    # Assert the balance was updated when the amount is positive
    new_balance = start_balance + amount
    user_mock.reference.update.assert_called_once_with(
        {'balance': new_balance})


@pytest.mark.parametrize("amount", [
    (-1),  # negative with one digit
    (-10),  # negative with two digits
    (-100),  # negative with three digits
    (-1000),  # negative with four digits
    (-10000000000000),  # huge negative number
])
def test_update_user_balance_negative_amount(unsecure_class, mock_firestore, amount):
    """Test update_user_balance for Unsecure class with negative amounts."""

    # Mock user document
    user_mock = mock.MagicMock()
    start_balance = 100
    user_mock.to_dict.return_value = {'balance': start_balance}
    mock_firestore.collection.return_value.where.return_value.limit.return_value.get.return_value = [
        user_mock]

    # Call the method with test wallet_number and amount
    wallet_number = 1
    unsecure_class.update_user_balance(wallet_number, amount)

    # Assert update was not called when the amount is negative
    user_mock.reference.update.assert_not_called()
