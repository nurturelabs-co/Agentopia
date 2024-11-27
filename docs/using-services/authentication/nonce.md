# Understanding and Managing Nonces

## What is a Nonce?
A nonce is a number that is used only once in cryptographic communication. In Agentopia's authentication system, the nonce is combined with the platform's message to create a unique message for signing. This allows you to invalidate previous signatures and maintain control over your authentication.

## Significance in Authentication
When generating a signature for authentication:
1. The platform message is combined with your current nonce value
2. This combined message is what you sign with your private key
3. The signature proves both your ownership of the wallet and that this is a fresh authentication attempt

## Managing Your Nonce
If you are using the Agentopia SDK, it automatically manages your nonce for you. However, if you are interacting with the API directly, you can follow these steps to manage your nonce:

### Getting Your Current Nonce
You can retrieve your current nonce value using the nonce endpoint:
```python
import requests

response = requests.get("https://api.agentopia.xyz/v1/user/{address}/nonce")
nonce = response.json()["nonce"]
```
### Incrementing Your Nonce
To invalidate your previous signature, you can increment your nonce value. This can be done using the following endpoint:
```python
response = requests.post("https://api.agentopia.xyz/v1/user/{address}/nonce")
new_nonce = response.json()["nonce"]
``` 

