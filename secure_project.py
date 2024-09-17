import os
import base64
import json
from datetime import datetime, timedelta, timezone

import firebase_admin
from firebase_admin import credentials, firestore

from google.cloud import pubsub_v1
from google.cloud.firestore_v1.base_query import FieldFilter


class Secure:
    def __init__(self, project_id, app_name, unsecure_db):
        # Get encoded Private key of Secure project
        encoded_key = os.getenv('GOOGLE_APPLICATION_CREDENTIALS_BASE64_SECURE')
        decoded_key = base64.b64decode(encoded_key)
        service_account_info = json.loads(decoded_key)
        cred = credentials.Certificate(service_account_info)

        app = firebase_admin.initialize_app(
            cred, {'projectId': project_id}, name=app_name)

        self.db = firestore.client(app=app)

        self.project_id = project_id

        self.publisher = pubsub_v1.PublisherClient()

        self.wallet_number = 1  # start wallet number from 1

        self.unsecure_db = unsecure_db

    def find_available_wallet(self):
        """Find an available wallet (not rented)"""

        wallet_query = self.db.collection('wallets').where(
            filter=FieldFilter('is_rented', '==', False)).limit(1).stream()
        wallet = next(wallet_query, None)

        return wallet

    def create_wallet(self):
        """Create a new wallet in the secure project with private data"""

        wallet_ref = self.db.collection('wallets').document()

        wallet_uid = wallet_ref.id
        wallet_number = self.wallet_number

        wallet_data = {
            'wallet_uid': wallet_uid,
            'number': wallet_number,
            'balance': 0,
            'is_rented': True,
            # 5 minutes rental
            'rental_expiry': datetime.now(timezone.utc) + timedelta(minutes=5)
        }

        wallet_ref.set(wallet_data)

        self.wallet_number += 1  # next wallet number

        return wallet_uid, wallet_number

    def rent_wallet(self, uid):
        """Find or create a wallet and rent it to a user for 5 minutes"""

        wallet = self.find_available_wallet()

        if wallet:
            wallet_data = wallet.to_dict()
            wallet_number = wallet_data['number']
            wallet_ref = wallet.reference
            wallet_ref.update({
                'is_rented': True,
                'rental_expiry': datetime.now(timezone.utc) + timedelta(minutes=5)
            })
        else:
            # No available wallet, create a new one
            wallet_uid, wallet_number = self.create_wallet()
            wallet_data = {'wallet_uid': wallet_uid, 'number': wallet_number}

        # Send wallet number to the unsecure project
        self.unsecure_db.link_wallet_to_user(uid, wallet_number)

        return wallet_data['number']

    def deposit_to_wallet(self, wallet_number, amount):
        """Deposit funds to the wallet and update the balance"""

        if amount < 0:
            print("The amount is less than 0, it can't be updated.")
        else:
            wallet_ref = self.db.collection('wallets').where(
                filter=FieldFilter('number', '==', wallet_number)).limit(1).get()

            if wallet_ref:
                wallet = wallet_ref[0]  # Get the first matching document
                wallet_data = wallet.to_dict()
                rental_expiry = wallet_data.get('rental_expiry')
                current_time = datetime.now(timezone.utc)

                # Update wallet balance
                new_balance = wallet_data['balance'] + amount
                wallet.reference.update({'balance': new_balance})

                # Check if the wallet is within the rental period
                if rental_expiry and current_time < rental_expiry:
                    # Send deposit amount to the unsecure project
                    self.unsecure_db.update_user_balance(
                        wallet_data['number'], amount
                    )
                    wallet.reference.update(
                        {'is_rented': False})  # Expire the wallet
                    self.unsecure_db.unlink_wallet_from_user(
                        wallet_data['number'])
                else:
                    print(f"Rental period expired. Deposit only updated in wallet.")
