# Check Your Agentopia Wallet Balance
You can check your wallet balance at any time to ensure it has sufficient funds for service usage.

=== "Using Agentopia API"
    Learn how to [generate a Authorization Code](authentication/generate-signature.md) to authenticate your wallet.
    ```bash
    curl -X GET \
    -H "Authorization: Basic AuthorizationCode" \
    https://api.agentopia.xyz/v1/balance
    ```
=== "Python SDK"
    ```bash
    pip install agentopia
    ```
    ```python
    from agentopia import Agentopia
    agentopia = Agentopia(private_key="your_private_key")
    balance = agentopia.get_balance()
    ```
Expected Response:

```json     
{
  "available_balance": 1000000,
  "amount_on_hold": 0
}
```
