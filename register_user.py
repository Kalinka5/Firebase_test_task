import functions_framework
import json


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
def register_user(request):
    try:
        # Parse request body for uid
        request_json = request.get_json()
        uid = request_json['uid']  # Extract the 'uid' parameter

        # Register the user in the unsecure system
        unsecure_db.register_user(uid)

        # Return success response
        response = {
            "status": "success",
            "message": f"User with UID {uid} registered successfully",
            "uid": uid
        }

        return (json.dumps(response), 200, {'Content-Type': 'application/json'})

    except KeyError:
        # Handle missing 'uid' parameter
        response = {
            "status": "error",
            "message": "Missing parameter: 'uid'"
        }
        return (json.dumps(response), 400, {'Content-Type': 'application/json'})

    except Exception as e:
        # Handle any other errors
        response = {
            "status": "error",
            "message": str(e)
        }
        return (json.dumps(response), 500, {'Content-Type': 'application/json'})
