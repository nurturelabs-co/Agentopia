# Generate Signature for Authentication
To access services on Agentopia, you need to authenticate your wallet using a signature. This ensures secure, decentralized, and tamper-proof transactions. Follow this guide to generate and use your signature for authenticated requests.

## Why is a Signature Required?
Agentopia uses a wallet-based authentication system. Instead of traditional usernames and passwords, your wallet address and a cryptographically signed message authenticate your identity. This eliminates the need for centralized authentication and ensures secure, decentralized access.

## Steps to Generate a Signature

### Step 1: Retrieve the Message to Sign
Agentopia requires you to sign a specific message to authenticate your wallet. Fetch this message from the /v1/message_to_sign/ endpoint + your current [nonce value](nonce.md)

```python
import requests

response = requests.get("https://api.agentopia.xyz/v1/message_to_sign/")
message = response.json()["message"]

response = requests.get(f"https://api.agentopia.xyz/v1/user/{address}/nonce")
nonce = response.json()["nonce"]

message = f"{message}:{nonce}"
```
Expected Response:
```python
message = "Sign to verify your user address with Agentopia.xyz on Base Testnet and Mainnet:0"
```

### Step 2: Sign the Message Using Your Private Key
Use a cryptographic tool or library to sign the retrieved message. Here’s how to do it with popular tools:

=== "Using Web3.py (Python)"
    ```python
    from eth_account import Account
    from eth_account.messages import encode_defunct

    private_key = "your_private_key"
    message = "Sign to verify your user address with Agentopia.xyz on Base Testnet and Mainnet:0"

    # Encode and sign the message
    message_hash = encode_defunct(text=message)
    signed_message = Account.sign_message(message_hash, private_key)

    print(signed_message.signature.hex())  # This is your signature
    ```
=== "Using Cast Command (Command Line)"
    ```bash
    cast wallet sign --private-key "your_private_key"\
    "Sign to verify your user address with Agentopia.xyz on Base Testnet and Mainnet:0"
    ```

### Step 3: Add the Signature to the Authorization Header
Combine your wallet address and signature into a Basic authentication header:

Format: wallet_address:signature
Encode as Base64.
Example in Python:
```python
import base64

wallet_address = "0xYourWalletAddress"
signature = "0xYourSignature"

auth = f"{wallet_address}:{signature}"
auth_b64 = base64.b64encode(auth.encode("utf-8")).decode("utf-8")

print(f"Authorization: Basic {auth_b64}")
```
Example Header:
```
http
Authorization: Basic eHh4eHh4OjB4eHlvdXJzaWduYXR1cmU=
```

### Verify the Signature
Once the Authorization header is set, you can verify your signature by making an authenticated API call. For example, check your wallet balance:

```bash
curl -X GET \
  -H "Authorization: Basic eHh4eHh4OjB4eHlvdXJzaWduYXR1cmU=" \
  https://api.agentopia.xyz/v1/balance
```

## Common Issues
- Incorrect Signature: Ensure you use the correct private key to sign the message.
- Nonce Expired: Fetch a new message if your current nonce has expired.
- Invalid Authorization Header: Double-check the Base64 encoding of your wallet address and signature.

## Next Steps
Now that you’ve authenticated your wallet:

- [Check your balance](../check-balance.md)
- [Search for available services](../search.md)
- [Execute services](../run-proxy-api.md)
