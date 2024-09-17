# Implementing in Projects

## Get private keys of Secure and Unsecure projects

- In Secure Project Settings go to Service accounts and click on "Generate new private key" and save it in your project
- In Unsecure Project Settings go to Service accounts and click on "Generate new private key" and save it in your project

## Encode keys

To encode private keys on Linux or macOS use:
base64 -w 0 <secure_private_key_file.json>
base64 -w 0 <unsecure_private_key_file.json>

On Windows:
certutil -encode <secure_private_key_file.json>
certutil -encode <unsecure_private_key_file.json>

## Move all rows of code from register_user.py to main.py

## Send gcloud command in console (Register user function)

```
gcloud functions deploy register_user  --runtime python312   --trigger-http   --allow-unauthenticated   --project <project_id> --set-env-vars GOOGLE_APPLICATION_CREDENTIALS_BASE64_SECURE="<secure_private_key>",GOOGLE_APPLICATION_CREDENTIALS_BASE64_UNSECURE="<unsecure_private_key>"

In our case <project_id> = nifty-kayak-435509-d6
```

## Move all rows of code from rent_wallet.py to main.py

## Send gcloud command in console (Rent wallet function)

```
gcloud functions deploy rent_wallet  --runtime python312   --trigger-http   --allow-unauthenticated   --project <project_id> --set-env-vars GOOGLE_APPLICATION_CREDENTIALS_BASE64_SECURE="<secure_private_key>",GOOGLE_APPLICATION_CREDENTIALS_BASE64_UNSECURE="<unsecure_private_key>"

In our case <project_id> = xenon-sunspot-429207-s0
```

## Move all rows of code from make_deposit.py to main.py

## Send gcloud command in console (Make Deposit function)

```
gcloud functions deploy make_deposit  --runtime python312   --trigger-http   --allow-unauthenticated   --project <project_id> --set-env-vars GOOGLE_APPLICATION_CREDENTIALS_BASE64_SECURE="<encoded_secure_private_key>",GOOGLE_APPLICATION_CREDENTIALS_BASE64_UNSECURE="<encoded_unsecure_private_key>"

In our case <project_id> = xenon-sunspot-429207-s0
```

# Using

## Register user

```
curl -X POST  <function_url>  -H "Content-Type: application/json"   -d '{"uid": "<user_uid>"}'

In our case <function_url> = https://us-central1-nifty-kayak-435509-d6.cloudfunctions.net/register_user
```

## Rent wallet

```
curl -X POST <function_url>  -H "Content-Type: application/json"   -d '{"uid": "<user_uid>"}'

In our case <function_url> = https://us-central1-xenon-sunspot-429207-s0.cloudfunctions.net/rent_wallet
```

## Make deposit

```
curl -X POST <function_url>  -H "Content-Type: application/json"   -d '{  "wallet_number": <wallet_number>,"amount": <amount>}'

In our case <function_url> = https://us-central1-xenon-sunspot-429207-s0.cloudfunctions.net/make_deposit
```
