import functions_framework
import json


from unsecure_project import Unsecure
from secure_project import Secure


# Initialize Firestore DB and Pub/Sub
secure_project_id = "xenon-sunspot-429207-s0"
unsecure_project_id = "nifty-kayak-435509-d6"
secure_app_name = "secure_app"
unsecure_app_name = "unsecure_app"

# Initialize both projects
unsecure_db = Unsecure(unsecure_project_id, unsecure_app_name)
secure_db = Secure(secure_project_id, secure_app_name, unsecure_db)


@functions_framework.http
def make_deposit(request):
    try:
        # Parse request body
        request_json = request.get_json()
        wallet_number = request_json['wallet_number']
        amount = float(request_json['amount'])

        # Perform the deposit in the secure system
        secure_db.deposit_to_wallet(wallet_number, amount)

        # Return success response
        response = {
            "status": "success",
            "message": f"Deposited {amount} into wallet {wallet_number}"
        }
        return (json.dumps(response), 200, {'Content-Type': 'application/json'})

    except KeyError as e:
        # Handle missing parameters in the request
        response = {
            "status": "error",
            "message": f"Missing parameter: {str(e)}"
        }
        return (json.dumps(response), 400, {'Content-Type': 'application/json'})

    except Exception as e:
        # Handle any other errors
        response = {
            "status": "error",
            "message": str(e)
        }
        return (json.dumps(response), 500, {'Content-Type': 'application/json'})
