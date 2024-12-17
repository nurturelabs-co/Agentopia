# Handling Holds in Agentopia

Holds are a crucial part of Agentopia's payment system. They allow you to temporarily reserve funds from a user's wallet before providing your service, ensuring you can charge the appropriate amount afterward.

## Understanding Holds

A hold is a temporary reservation of funds that:
- Ensures the user has sufficient balance
- Prevents the funds from being used elsewhere
- Expires after a specified time
- Can be partially consumed or released

## Hold Lifecycle

1. **Creation**
   - User requests your service
   - Agentopia creates a hold for the specified amount
   - Hold ID is provided in the `X-Hold-Id` header

2. **Verification**
   - Your service verifies the hold exists and is valid
   - Checks if the hold amount is sufficient
   - Confirms the hold hasn't expired

3. **Consumption**
   - After providing the service, deduct the actual amount used
   - Release any unused funds back to the user
   - Hold becomes inactive after consumption

## Hold Management API

### Creating a Hold

```python
from agentopia import Agentopia

client = Agentopia()
hold_id = client.hold.create(
    service_id="your-service-id",
    amount=100000,  # 0.1 USDC
    expires_in=3600  # 1 hour
)
```

### Getting Hold Details

```python
hold = client.hold.get(hold_id)
print(f"Hold amount: {hold.amount}")
print(f"Expires at: {hold.expires_at}")
```

### Releasing a Hold with Charge

```python
client.hold.release(
    hold_id=hold_id,
    amount=50000,  # Charge 0.05 USDC
    input_json={"request_data": "..."},  # Optional
    result_json={"response_data": "..."}  # Optional
)
```

### Splitting a Hold

For services that need to share holds with other services:

```python
split_details = [
    {"service_id": "service-1", "amount": 30000},
    {"service_id": "service-2", "amount": 20000}
]
result = client.hold.split(hold_id, split_details)
```

## Best Practices

1. **Hold Amounts**
   - Request holds slightly larger than expected charges
   - Consider variable costs in your hold amount
   - Don't hold excessive amounts unnecessarily

2. **Expiration Times**
   - Set reasonable expiration times based on your service
   - Consider potential delays and processing time
   - Handle expired holds gracefully

3. **Error Handling**
   ```python
   try:
       hold = client.hold.get(hold_id)
       if hold.is_active and not hold.is_expired():
           # Process the request
           client.hold.release(hold_id, amount)
   except Exception as e:
       # Handle errors appropriately
       logger.error(f"Hold error: {e}")
   ```

4. **Monitoring and Logging**
   - Track hold creation and usage
   - Monitor hold expiration rates
   - Log hold-related errors for debugging

## Common Scenarios

### Dynamic Pricing

```python
@app.post("/process")
@payable(hold_amount=100000)  # Hold 0.1 USDC
async def process(request: Request, data: dict):
    # Calculate actual cost based on processing
    cost = calculate_cost(data)
    
    return JSONResponse(
        content={"result": "..."},
        headers={"X-Usdc-Used": str(cost)}
    )
```

### Long-Running Operations

```python
@app.post("/batch_process")
@payable(
    hold_amount=1000000,  # Hold 1 USDC
    hold_expires_in=7200  # 2 hours
)
async def batch_process(request: Request, items: List[dict]):
    # Process items and track costs
    total_cost = 0
    for item in items:
        cost = process_item(item)
        total_cost += cost
    
    return JSONResponse(
        content={"status": "complete"},
        headers={"X-Usdc-Used": str(total_cost)}
    )
```

## Security Considerations

1. Always verify hold ownership
2. Never expose hold IDs in public responses
3. Use appropriate error messages
4. Implement proper logging for auditing
5. Handle edge cases (expiration, insufficient funds)

Remember that holds are a critical part of your service's payment infrastructure. Proper hold management ensures both you and your users have a smooth experience with fair and transparent charging.
