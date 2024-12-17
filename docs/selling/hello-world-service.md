# Hello World! Service Example

This guide demonstrates how to create a simple "Hello World" service using Agentopia. We'll walk through creating a basic FastAPI service that charges users for each request.

## Service Configuration

First, define your service configuration:

```python
from schema import ServiceConfig

agentopia_config = ServiceConfig(
    name="Hello World Service",
    description="A simple service to demonstrate the Agentopia.xyz platform",
    slug="hello-world-service",
    default_hold_amount=10,  # 0.00001 USDC
    default_hold_expires_in=3600,  # 1 hour
    logo_url="https://res.cloudinary.com/dd9z3q1v8/image/upload/w_582,h_329,q_auto/v1734426055/hello_lqte9l.png",
)
```

## Create the FastAPI Application

Initialize your FastAPI app with the service configuration:

```python
from fastapi import FastAPI, Request

app = FastAPI(
    title=agentopia_config.name,
    description=agentopia_config.description,
    version="0.0.1",
)
```

## Implement the Endpoint

Create a simple endpoint that returns a greeting:

```python
from agentopia import payable
from fastapi.responses import JSONResponse

@app.get("/hello_world")
@payable(
    hold_amount=10,  # Hold 0.00001 USDC
    hold_expires_in=3600  # Hold for 1 hour
)
async def hello_world(request: Request):
    # Return a simple greeting and charge 1 micro USDC
    return JSONResponse(
        content={"message": "Hello from Agentopia!"},
        headers={"X-Usdc-Used": "1"}  # Charge 0.000001 USDC
    )
```

## Understanding the Code

Let's break down the key components:

1. **Service Configuration**
   - `name`: Display name for your service
   - `description`: Brief explanation of what your service does
   - `slug`: Unique identifier for your service
   - `default_hold_amount`: Default amount to hold (in micro USDC)
   - `default_hold_expires_in`: Default hold duration in seconds
   - `logo_url`: URL to your service's logo

2. **FastAPI Setup**
   - Creates a FastAPI application with your service details
   - Automatically generates OpenAPI documentation

3. **Endpoint Implementation**
   - Uses `@payable` decorator for payment processing
   - Holds 0.00001 USDC (10 micro USDC)
   - Charges 0.000001 USDC (1 micro USDC) per request
   - Returns a simple JSON response

## Testing the Service

1. Start your service:
```bash
uvicorn main:app --reload
```

2. Your service will be available at:
   - API Endpoint: `http://localhost:8000/hello_world`
   - Documentation: `http://localhost:8000/docs`

## Next Steps

1. Deploy your service
2. Register it with Agentopia
3. Monitor usage and earnings

This example demonstrates the basics of creating an Agentopia service. You can build upon this foundation to create more complex services with dynamic pricing, multiple endpoints, and advanced features.
