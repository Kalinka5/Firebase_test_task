import os
import base64
import json

import firebase_admin
from firebase_admin import credentials, firestore

from google.cloud.firestore_v1.base_query import FieldFilter


class Unsecure:
    def __init__(self, project_id, app_name):
        # Get encoded Private key of Unsecure project
        encoded_key = os.getenv(
            'GOOGLE_APPLICATION_CREDENTIALS_BASE64_UNSECURE')
        decoded_key = base64.b64decode(encoded_key)
        service_account_info = json.loads(decoded_key)
        cred = credentials.Certificate(service_account_info)

        app = firebase_admin.initialize_app(
            cred, {'projectId': project_id}, name=app_name)

        self.db = firestore.client(app=app)

    def register_user(self, uid):
        """Register a new user"""

        user_ref = self.db.collection('users').document(uid)

        user_ref.set({'uid': uid, 'balance': 0})

    def link_wallet_to_user(self, uid, wallet_number):
        """Link the wallet number to the user in the unsecure project"""

        user_ref = self.db.collection('users').document(uid)

        user_ref.update({'rented_wallet': wallet_number})

    def unlink_wallet_from_user(self, wallet_number):
        """Unlink the wallet from the user in the unsecure project"""

        try:
            user_ref = self.db.collection('users').where(filter=FieldFilter(
                'rented_wallet', '==', wallet_number)).limit(1).get()
            user = user_ref[0]  # Get the first matching document

            # Remove rented wallet
            user.reference.update({'rented_wallet': firestore.DELETE_FIELD})
        except IndexError:
            print(f"No wallet with {wallet_number} number!")

    def update_user_balance(self, wallet_number, amount):
        """Update the user's balance based on the wallet deposit"""

        if amount < 0:
            print("The amount is less than 0, it can't be updated.")
        else:
            user_ref = self.db.collection('users').where(filter=FieldFilter(
                'rented_wallet', '==', wallet_number)).limit(1).get()

            if user_ref:
                user = user_ref[0]
                user_data = user.to_dict()

                new_balance = user_data['balance'] + amount

                user.reference.update({'balance': new_balance})
            else:
                print(f"No user found with wallet {wallet_number}")
