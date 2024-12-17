# Using Services Directly

Once you have [set up your wallet](wallet-setup.md) and [created an API key](authentication/create-api-key.md), you can call services directly by creating a hold first and then making the API call with the hold ID.

## Making Direct API Calls

### Using Python SDK

=== "Python SDK"
    ```python
    from agentopia import Agentopia
    
    # Initialize client
    agentopia = Agentopia(private_key="your_private_key")
    
    # Call service endpoint directly
    response = agentopia.service.execute(
        service_slug="service-slug",  # The unique service identifier
        endpoint_path="endpoint/path", # The API endpoint path
        method="GET",                 # HTTP method
        params={"param1": "value1"}   # Optional query parameters
    )
    ```

The `execute()` method handles creating the hold and making the direct API call for you. Under the hood, it:

1. Gets the service details and default hold amount
2. Creates a hold using the service ID
3. Makes the API call directly to the service with the hold ID in the header
4. Returns the response from the service

### Manual Hold Creation and API Call

If you need more control, you can create the hold manually and make the direct call yourself:

=== "Python SDK"
    ```python
    from agentopia import Agentopia
    from decimal import Decimal
    
    agentopia = Agentopia(private_key="your_private_key")
    
    # Get service details
    service = agentopia.service.get_by_slug("service-slug")
    
    # Create a hold
    hold_id = agentopia.hold.create(
        service_id=service.id,
        amount=int(Decimal(str(service.default_hold_amount))), 
        expires_in=service.default_hold_expires_in
    )
    
    # Make direct API call with hold ID in header
    import httpx
    
    headers = {"X-Hold-Id": str(hold_id)}
    endpoint = "/endpoint/path"
    
    with httpx.Client() as client:
        response = client.get(
            f"{service.base_url}{endpoint}",
            headers=headers,
            params={"param1": "value1"}
        )
        result = response.json()
    ```

## Payment and Holds

When making direct API calls:

1. You must create a hold first - this reserves funds from your wallet
2. The hold ID must be included in the `X-Hold-Id` header when calling the service
3. The service will validate the hold and deduct the actual usage amount
4. Any remaining hold amount is automatically released after expiration

You can check your balance and holds using:

=== "Python SDK"
    ```python
    balance = agentopia.get_balance()
    print(f"Available: {balance.available_balance}")
    print(f"On Hold: {balance.amount_on_hold}")
    ```

## Error Handling

Handle these common errors when making direct calls:

- Invalid or expired hold ID
- Insufficient balance for creating hold
- Service unavailable
- Invalid parameters
- Network errors when calling service directly

Always implement proper error handling and consider using the SDK's `execute()` method which handles many edge cases automatically.
