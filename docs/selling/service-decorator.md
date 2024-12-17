# Using the `@service` Decorator

The `@payable` decorator is a key component of Agentopia that enables payment processing for your API endpoints. It handles the hold verification, payment processing, and automatic charge deduction.

## Basic Usage

Here's how to use the `@payable` decorator:

```python
from agentopia import payable
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

@app.get("/my_endpoint")
@payable(
    hold_amount=100000,  # Amount in micro USDC (0.1 USDC)
    hold_expires_in=3600  # Hold expiration in seconds (1 hour)
)
async def my_endpoint(request: Request):
    # Your endpoint logic here
    return JSONResponse(
        content={"message": "Success!"},
        headers={"X-Usdc-Used": "1"}  # Charge 0.000001 USDC
    )
```

## Parameters

- `hold_amount`: The amount to hold in micro USDC (6 decimal places)
  - Example: `100000` = 0.1 USDC
  - This is the maximum amount that can be charged for this request
  
- `hold_expires_in`: Time in seconds before the hold expires
  - Default: 3600 (1 hour)
  - After expiration, the hold becomes invalid

## Response Headers

The decorator looks for the `X-Usdc-Used` header in your response to determine how much to charge the user:

```python
headers={"X-Usdc-Used": "1"}  # Charge 0.000001 USDC
```

If no header is provided, it defaults to charging 1 micro USDC.

## Error Handling

The decorator automatically handles several error cases:

- Missing hold ID: Returns 402 Payment Required
- Invalid hold ID: Returns 402 Payment Required
- Hold verification failure: Returns 402 Payment Required
- Payment processing failure: Returns 500 Internal Server Error

## Local Development

For local development, you can enable `AGENTOPIA_LOCAL_MODE` in your environment to bypass hold verification:

```bash
export AGENTOPIA_LOCAL_MODE=true
```

## Best Practices

1. Set reasonable hold amounts
   - Hold amount should cover your maximum expected charge
   - Don't set unnecessarily high holds as it locks user funds

2. Choose appropriate expiration times
   - Set expiration based on your expected processing time
   - Longer operations need longer hold times

3. Be precise with charges
   - Always specify exact charges via `X-Usdc-Used`
   - Charge only for actual usage

4. Handle errors gracefully
   - Catch and handle payment-related exceptions
   - Provide clear error messages to users

## Example: Dynamic Charging

Here's an example of dynamic charging based on usage:

```python
@app.post("/process_text")
@payable(hold_amount=100000, hold_expires_in=3600)
async def process_text(request: Request, text: str):
    # Calculate charge based on text length
    char_count = len(text)
    charge = max(1, char_count // 100)  # 1 micro USDC per 100 chars
    
    result = process_text_somehow(text)
    
    return JSONResponse(
        content={"result": result},
        headers={"X-Usdc-Used": str(charge)}
    )
```

This example charges based on the input text length, with a minimum charge of 1 micro USDC.
