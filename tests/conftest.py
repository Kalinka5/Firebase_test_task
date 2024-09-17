import pytest
from unittest import mock

from unsecure_project import Unsecure
from secure_project import Secure


@pytest.fixture
def mock_firestore():
    """Mock Firestore database."""
    return mock.MagicMock()


@pytest.fixture
def mock_pubsub():
    """Mock Pub/Sub publisher."""
    return mock.MagicMock()


@pytest.fixture
def mock_unsecure():
    """Mock Unsecure instance passed to Secure."""
    return mock.MagicMock()


@pytest.fixture
def mock_firebase_init():
    """Mock firebase_admin.initialize_app to avoid reinitializing Firebase."""
    with mock.patch('firebase_admin.initialize_app') as mock_init:
        yield mock_init


@pytest.fixture
def mock_firebase_credentials():
    """Mock firebase_admin credentials."""
    with mock.patch('firebase_admin.credentials.Certificate') as mock_cred:
        yield mock_cred


@pytest.fixture
def secure_class(mock_firestore, mock_pubsub, mock_unsecure, mock_firebase_init, mock_firebase_credentials):
    """Fixture for the Secure class."""
    with mock.patch('firebase_admin.firestore.client', return_value=mock_firestore):
        with mock.patch('google.cloud.pubsub_v1.PublisherClient', return_value=mock_pubsub):
            yield Secure(project_id='secure_project', app_name='secure_app_test', unsecure_db=mock_unsecure)


@pytest.fixture
def unsecure_class(mock_firestore, mock_firebase_init, mock_firebase_credentials):
    """Fixture for the Unsecure class."""
    with mock.patch('firebase_admin.firestore.client', return_value=mock_firestore):
        yield Unsecure(project_id='unsecure_project', app_name='unsecure_app_test')
