import functions_framework
import threading
import time
from firebase_admin import firestore
from google.cloud.firestore_v1.base_query import FieldFilter


from projects.unsecure_project import Unsecure
from projects.secure_project import Secure


# Initialize Firestore DB and Pub/Sub
secure_project_id = "xenon-sunspot-429207-s0"
unsecure_project_id = "nifty-kayak-435509-d6"
secure_app_name = "secure_app"
unsecure_app_name = "unsecure_app"

# Initialize both projects
unsecure_db = Unsecure(unsecure_project_id, unsecure_app_name)
secure_db = Secure(secure_project_id, secure_app_name, unsecure_db)


@functions_framework.http
def rent_wallet(request):
    """HTTP function to rent a wallet for a user for 5 minutes"""
    request_json = request.get_json(silent=True)
    uid = request_json.get('uid')

    if not uid:
        return {'status': 'failed', 'message': 'UID is required'}, 400

    # Rent a wallet from the secure project
    wallet_number = secure_db.rent_wallet(uid)

    # Start a thread to expire the wallet after 5 minutes
    thread = threading.Thread(
        target=expire_wallet_after_timeout, args=(uid, wallet_number, 5))
    thread.start()

    return {'status': 'success', 'walletNumber': wallet_number}, 200


def expire_wallet_after_timeout(uid, wallet_number, timeout_minutes):
    """Expire the wallet after a timeout"""
    # Wait for the rental period to expire (5 minutes in this case)
    time.sleep(timeout_minutes * 60)

    # Check if the wallet still exists and hasn't already been updated
    wallet_query = secure_db.db.collection('wallets').where(
        filter=FieldFilter('number', '==', wallet_number)).limit(1).stream()
    wallet = next(wallet_query, None)

    if wallet:
        wallet_data = wallet.to_dict()

        # Check if the wallet is still rented and if the rental has expired
        if wallet_data.get('is_rented', False):
            wallet_ref = wallet.reference
            wallet_ref.update({'is_rented': False})  # Expire the wallet

            # Unlink the wallet from the user in the unsecure project
            user_ref = unsecure_db.db.collection('users').document(uid)
            # Remove rented wallet
            user_ref.update({'rented_wallet': firestore.DELETE_FIELD})

            print(f"Wallet {wallet_number} expired for user {uid}")
        else:
            print(f"Wallet {wallet_number} already expired for user {uid}")
