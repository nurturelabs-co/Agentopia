# Wallet Setup: Getting Started with Agentopia

To use services on Agentopia, you need a wallet funded with USDC. Agentopia's wallet system ensures seamless and secure payment handling, allowing AI agents and users to interact with services autonomously.

This guide walks you through setting up your wallet, funding it with USDC, and approving payments for service usage.

## Step 1: Create Your Wallet

You can create and manage your wallet directly through Agentopia's Wallet Dashboard or using Web3 tools. Follow these steps:

### Option 1: Use the Agentopia Wallet Dashboard

1. Visit the [Agentopia Wallet Dashboard](https://agentopia.xyz/dashboard)
2. Sign in with your preferred wallet (e.g., MetaMask, WalletConnect)
3. Your wallet is now linked to Agentopia, and you can start using it

### Option 2: Use Web3 Tools

For developers or advanced users, create a wallet or link an existing one using Ethereum-compatible tools such as web3.py or cast.

## Step 2: Fund Your Wallet with USDC

Services on Agentopia use USDC for transactions. Here's how to fund your wallet:

### Using a Crypto Exchange

1. Purchase USDC from an exchange (e.g. Coinbase, Binance)
2. Transfer USDC to your wallet address

## Step 3: Deposit USDC into your Agentopia Account

You'll need to approve USDC for the [Agentopia MicroPayment Contract](../contracts.md) and then call the deposit function on the [Agentopic Micropayment Contract](../contracts.md)

=== "Using Cast Command"

    ```bash
    cast call 0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913 \
    --rpc-url https://mainnet.base.org \
    "approve(address,uint256)" 0xaEF2fc1f54AE5b260cA2123B27bE6E79C3AAFa7a 1000000 \
    --private-key $PRIVATE_KEY

    cast call 0xaEF2fc1f54AE5b260cA2123B27bE6E79C3AAFa7a \
    --rpc-url https://mainnet.base.org \
    "deposit(uint256)" 1000000 \
    --private-key $PRIVATE_KEY
    ```
=== "Python SDK"
    ```bash
    pip install agentopia
    ```
    ```python
    from agentopia import Agentopia
    agentopia = Agentopia(private_key="your_private_key")
    agentopia.deposit(1000000)
    ```

This approves $1 (1,000,000 micro USDC) and then deposits $1 to the Agentopia Micropayment Contract.
Note: the number used in the cast call is in micro USDC. ie. 1 USDC = 1,000,000 micro USDC.

## Step 4: Verify Your Agentopia Wallet Balance
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
