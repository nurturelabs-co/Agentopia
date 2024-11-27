# Selling via Agentopia: Overview

Agentopia makes it simple for developers to monetize their APIs and services by integrating them into the Agentopia ecosystem. By connecting your API, you can automatically handle payments, manage usage, and track earnings—all with minimal setup.

This guide will walk you through how to integrate your API, define usage costs, and register your service on Agentopia.

## Why Sell Your API on Agentopia?

- **Instant Monetization**: Charge users per request, with payments handled automatically via USDC.
- **Hassle-Free Integration**: Use your preferred API framework (e.g., FastAPI) with built-in support for Agentopia.
- **Transparent Usage Metrics**: Track service usage and earnings through a comprehensive dashboard.
- **Autonomous AI Compatibility**: Your service becomes instantly accessible to AI agents for automated usage.

## Key Steps to Monetize Your API

1. **Set Up Your API**: Use any framework to create your API. (We recommend FastAPI for its simplicity and performance.)
2. **Define Costs**: Specify how much users will be charged for each endpoint or service.
3. **Integrate with Agentopia SDK**: Add the necessary hooks to manage payments and usage metrics.
4. **Register Your Service**: List your API on Agentopia to start earning from users and AI agents.
5. **Track Usage and Earnings**: Access real-time stats via the Agentopia dashboard.

## Example: Connecting Your API to Agentopia

Here's a simple example of an API endpoint that charges users $0.000001 (1 micro USDC) per request using Agentopia's SDK:

```python
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from agentopia import payable

app = FastAPI()

@app.get("/hello_world")
@payable(
    hold_amount=100000, hold_expires_in=3600
)  # Hold $0.1 in the user's account for 1 hour
async def hello_world(
    request: Request,
):
    print("Executing hello_world endpoint")
    # Execute the service and charge the user $0.000_001
    print("Preparing response with $0.000001 charge")
    response = JSONResponse(
        content={"message": "Hello from Agentopia!"}, headers={"X-Usdc-Used": "1"}
    )
    print("Returning response")
    return response
```

## What's Happening in the Example?

- **Hold Amount**: The `@payable` decorator specifies a hold of $0.10 (100,000 micro USDC) in the user's wallet for 1 hour.
- **Charge**: Once the endpoint is executed, the service deducts $0.000001 from the user's account.
- **Response**: The `X-Usdc-Used` header in the response confirms the amount charged for the service.

## Benefits of Agentopia Integration

- **Automated Payments**: Agentopia handles the payment process, including holds, deductions, and refunds if needed.
- **Secure Transactions**: Built on blockchain technology, ensuring transparency and trust.
- **Customizable Pricing**: You define the hold amount and charges for each endpoint, giving you full control over monetization.
- **Developer Dashboard**: Monitor service usage, track earnings, and update configurations through an intuitive dashboard.

## Next Steps

1. [Learn how to configure API payments](#)
2. [Register your service on Agentopia](#) 
3. [Monitor usage and earnings](#)

Start monetizing your APIs with Agentopia today and unlock new revenue streams for your services!
