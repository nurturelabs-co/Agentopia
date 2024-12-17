# Using Services via Proxy API

Once you have [set up your wallet](wallet-setup.md) and [created an API key](authentication/create-api-key.md), you can start using services through Agentopia's proxy API.

## Making API Calls

### Using Python SDK

=== "Python SDK"
    ```python
    from agentopia import Agentopia
    
    # Initialize client
    agentopia = Agentopia(private_key="your_private_key")
    
    # Call service endpoint
    response = agentopia.service.execute_via_proxy(
        service_slug="service-slug",  # The unique service identifier
        endpoint_path="endpoint/path", # The API endpoint path
        method="GET",                 # HTTP method
        params={"param1": "value1"}   # Optional query parameters
    )
    ```

### Example: Using X.com Service

Here's an example of using the X.com service to fetch user details:

=== "Python SDK"
    ```python
    from agentopia import Agentopia
    
    agentopia = Agentopia(private_key="your_private_key")
    
    # Get user details
    response = agentopia.service.execute_via_proxy(
        service_slug="x-com-service",
        endpoint_path="user/details",
        method="GET",
        params={"username": "elonmusk"}
    )
    
    print(response)
    # Example output:
    # {
    #     "username": "elonmusk",
    #     "follower_count": 1000000,
    #     "following_count": 500,
    #     "description": "..."
    # }
    ```

### Search Tweets Example

=== "Python SDK"
    ```python
    # Search tweets
    response = agentopia.service.execute_via_proxy(
        service_slug="x-com-service",
        endpoint_path="search/tweets",
        method="GET",
        params={
            "query": "bitcoin",
            "section": "top",
            "limit": 5
        }
    )
    ```

## Payment and Holds

When you make an API call:

1. The service will place a hold on your wallet for the specified amount (e.g., $0.1 USDC)
2. The hold expires after a set duration (e.g., 10 minutes)
3. After successful execution, the actual used amount is deducted from the hold
4. Any remaining amount is released back to your available balance

You can check your balance and holds using:

=== "Python SDK"
    ```python
    balance = agentopia.get_balance()
    print(f"Available: {balance.available_balance}")
    print(f"On Hold: {balance.amount_on_hold}")
    ```

## Error Handling

The SDK will raise exceptions for common errors:

- Insufficient balance
- Invalid API key
- Service unavailable
- Invalid parameters

Always implement proper error handling in your code when making service calls.
