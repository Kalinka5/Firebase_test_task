from unittest import mock

import pytest

from firebase_admin import firestore


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
def test_register_user_non_existing_user(user_uid, unsecure_class, mock_firestore):
    """Test register_user for Unsecure class with different data types."""
    user_ref_mock = mock.MagicMock()
    mock_firestore.collection.return_value.document.return_value = user_ref_mock

    unsecure_class.register_user(uid=user_uid)

    user_ref_mock.set.assert_called_once_with(
        {'uid': user_uid, 'balance': 0})


def test_register_existing_user(unsecure_class, mock_firestore):
    """Test registering a user when the user already exists"""

    uid = "existing_user_001"
    # Simulate Firestore behavior where the user already exists
    mock_firestore.collection('users').document(
        uid).get.return_value.exists = True

    unsecure_class.register_user(uid)

    # Ensure that Firestore overwrite the document if it already exists
    mock_firestore.collection('users').document(
        uid).set.assert_called_with({'uid': uid, 'balance': 0})


@pytest.mark.parametrize("wallet_number", [
    (0),  # zero
    (1),  # one digit
    (2.4),  # float number
    (-5.4),  # float number
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


def test_link_wallet_to_non_existing_user(unsecure_class, mock_firestore):
    """Test linking wallet to user when the user document doesn't exist"""

    uid = "non_existing_user"
    wallet_number = 1111

    # Simulate Firestore behavior where the user doesn't exist
    mock_firestore.collection('users').document(
        uid).get.return_value.exists = False

    unsecure_class.link_wallet_to_user(uid, wallet_number)

    # Verify that update is still attempted even if user doesn't exist
    mock_firestore.collection('users').document(
        uid).update.assert_called_with({'rented_wallet': wallet_number})


@pytest.mark.parametrize("wallet_number", [
    (0),  # zero
    (1),  # one digit
    (2.4),  # float number
    (-5.4),  # float number
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


def test_unlink_wallet_from_non_existing_wallet(unsecure_class, mock_firestore):
    """Test unlinking wallet when no user has the given wallet number"""

    wallet_number = 9999

    # Simulate Firestore where no user is found with the given wallet number
    mock_firestore.collection.return_value.where.return_value.limit.return_value.get.return_value = []

    unsecure_class.unlink_wallet_from_user(wallet_number)

    # Ensure no Firestore update is attempted if no matching user is found
    mock_firestore.collection('users').document().update.assert_not_called()


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


# Test updating user balance with no matching wallet number
def test_update_user_balance_no_wallet(unsecure_class, mock_firestore):
    wallet_number = 6666
    deposit_amount = 50
    # Simulate Firestore behavior where no user has the given wallet number
    mock_firestore.collection.return_value.where.return_value.limit.return_value.get.return_value = []

    unsecure_class.update_user_balance(wallet_number, deposit_amount)

    # Ensure no Firestore update is attempted if no matching user is found
    mock_firestore.collection('users').document().update.assert_not_called()


# Test unlinking wallet from user when multiple users are found with the wallet number
def test_unlink_wallet_multiple_users_found(unsecure_class, mock_firestore):
    wallet_number = 7777
    # Simulate Firestore where multiple users are found with the given wallet number
    mock_user1 = mock.MagicMock()
    mock_user2 = mock.MagicMock()
    mock_firestore.collection.return_value.where.return_value.limit.return_value.get.return_value = [
        mock_user1, mock_user2]

    unsecure_class.unlink_wallet_from_user(wallet_number)

    # Ensure that the first user's rented_wallet is unlinked (limit=1 should guarantee one update)
    mock_user1.reference.update.assert_called_with(
        {'rented_wallet': firestore.DELETE_FIELD})
    # Ensure no updates to the second user
    mock_user2.reference.update.assert_not_called()
