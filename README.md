# Installation 📄

### 1. Clone the repository:
   ```bash
   git clone https://github.com/Kalinka5/Firebase_test_task.git
   ```
### 2. Create a virtual environment and activate it:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```
### 3. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

___

# 🚀 Implementing in Projects

## 1) Get private keys of Secure and Unsecure projects

- In *Secure* **Project Settings** go to **Service accounts** and click on **"Generate new private key"** and save it in your project
- In *Unsecure* **Project Settings** go to **Service accounts** and click on **"Generate new private key"** and save it in your project

## 2) Encode keys

To encode private keys on **Linux** or **macOS** use:

```
base64 -w 0 <secure_private_key_file.json>
```
```
base64 -w 0 <unsecure_private_key_file.json>
```

On **Windows**:

```
certutil -encode <secure_private_key_file.json>
```
```
certutil -encode <unsecure_private_key_file.json>
```

## 3) Move all rows of code from *register_user.py* to *main.py*

## 4) Send *gcloud command* in console (Register user function)

```
gcloud functions deploy register_user  --runtime python312   --trigger-http   --allow-unauthenticated   --project <project_id> --set-env-vars GOOGLE_APPLICATION_CREDENTIALS_BASE64_SECURE="<secure_private_key>",GOOGLE_APPLICATION_CREDENTIALS_BASE64_UNSECURE="<unsecure_private_key>"
```
In our case:
- **project_id** = nifty-kayak-435509-d6
- **secure_private_key** = Your encoded secure private key
- **unsecure_private_key** = Your encoded unsecure private key

## 5) Move all rows of code from *rent_wallet.py* to *main.py*

## 6) Send *gcloud command* in console (Rent wallet function)

```
gcloud functions deploy rent_wallet  --runtime python312   --trigger-http   --allow-unauthenticated   --project <project_id> --set-env-vars GOOGLE_APPLICATION_CREDENTIALS_BASE64_SECURE="<secure_private_key>",GOOGLE_APPLICATION_CREDENTIALS_BASE64_UNSECURE="<unsecure_private_key>"
```
In our case:
- **project_id** = xenon-sunspot-429207-s0
- **secure_private_key** = Your encoded secure private key
- **unsecure_private_key** = Your encoded unsecure private key

## 7) Move all rows of code from *make_deposit.py* to *main.py*

## 8) Send *gcloud command* in console (Make Deposit function)

```
gcloud functions deploy make_deposit  --runtime python312   --trigger-http   --allow-unauthenticated   --project <project_id> --set-env-vars GOOGLE_APPLICATION_CREDENTIALS_BASE64_SECURE="<encoded_secure_private_key>",GOOGLE_APPLICATION_CREDENTIALS_BASE64_UNSECURE="<encoded_unsecure_private_key>"
```
In our case:
- **project_id** = xenon-sunspot-429207-s0
- **secure_private_key** = Your encoded secure private key
- **unsecure_private_key** = Your encoded unsecure private key

___

# 🛠️ Using

Send **POST** requests to *Firebase function*:

## Register user

```
curl -X POST  <function_url>  -H "Content-Type: application/json"   -d '{"uid": "<user_uid>"}'
```
In our case:
- **function_url** = https://us-central1-nifty-kayak-435509-d6.cloudfunctions.net/register_user
- **user_uid** = 1

## Result (Successfull JSON response):
{"status": "success", "message": "User with UID 1 registered successfully", "uid": "1"}

## Rent wallet

```
curl -X POST <function_url>  -H "Content-Type: application/json"   -d '{"uid": "<user_uid>"}'
```
In our case:
- **function_url** = https://us-central1-xenon-sunspot-429207-s0.cloudfunctions.net/rent_wallet
- **user_uid** = 1

## Result (Successfull JSON response):
{"status":"success","walletNumber":1}

## Make deposit

```
curl -X POST <function_url>  -H "Content-Type: application/json"   -d '{  "wallet_number": <wallet_number>,"amount": <amount>}'
```
In our case:
- **function_url** = https://us-central1-xenon-sunspot-429207-s0.cloudfunctions.net/make_deposit
- **wallet_number** = 1
- **amount** = 200

## Result (Successfull JSON response):
{"status": "success", "message": "Deposited 200.0 into wallet 1"}

# ✅ Testing

## Using 

Write in console this command:
```
pytest --cov
```

## Result

![image](https://github.com/user-attachments/assets/f73c65c5-dc20-4e28-bb7c-3b46bba8db7b)


