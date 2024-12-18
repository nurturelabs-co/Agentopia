# Agentopia [![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/release/python-3100/) [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<img alt="Logo" align="right" src="https://raw.githubusercontent.com/nurturelabs-co/Agentopia/main/logo.png" width="20%" />

- Add superpowers to your AI agent. Our SDK empowers AI agents to discover and pay for services, products, and other agents on demand—seamlessly and autonomously.
- Devs, you can easily:
  - Add new capabilities to your AI agent 10x faster
  - Discover and pay for services, APIs, data set or infra your AI agent needs
  - Pay with USDC automatically, no credit cards or bank account needed
  - Build your own services to sell to AI agents
  - Remix existing services into new offerings
  - Skip lengthy approval processes, no permissions required
  - Start earning revenue immediately

## Contents
- [Installation](#install-the-sdk)
- [Using Services](#use-a-service-on-agentopia)
  - [Funding Your Wallet](#fund-your-agentopia-wallet)
  - [Service Usage](#use-a-service)
- [Selling your Services](#sell-your-service-on-agentopia)
  - [Hello World Example](#hello-world-service)
  - [Open Router Example](#open-router-service)
  - [Service Registration](#register-your-service)
  - [Withdraw earnings](#withdraw-earnings-from-agentopia-wallet)
- [Contact](#contact-us)

## Install the SDK

```bash
pip install agentopia
```

## Use a service on Agentopia

Search and use services on Agentopia Marketplace. You can can pay for services with USDC on Base blockchain, with usage-based pricing.

### Fund your Agentopia Wallet

```python
from agentopia import Agentopia
agentopia_client = Agentopia(private_key="your_private_key")
agentopia_client.deposit(amount=1000_000)
```

This will initiate a deposit of 1 USDC (the values used in the SDK are in micro USDC) request which will be processed in a few minutes on the base blockchain.

### Use a service

```python
from agentopia import Agentopia
agentopia_client = Agentopia(private_key="your_private_key")
response = agentopia_client.service.execute_via_proxy(
    service_slug="hello-world", endpoint_path="hello_world", method="GET"
)
print(response)
```

## Sell your service on Agentopia

Build and sell API/data services on the Agentopia Marketplace. AI agents and users can pay for your service with USDC on Base blockchain.

Below are some example services using the Agentopia SDK.

### Hello World Service
You can enable agentopia payments in your endpoints simply by adding the `@payable` decorator and returning the response with the `X-Usdc-Used` header.
```python
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from agentopia import payable

app = FastAPI()

@app.get("/hello_world")
@payable(
    hold_amount=100000, hold_expires_in=3600
)  # Hold 0.1 USDC in the users account for 1hr
async def hello_world(
    request: Request,
):
    print("Executing hello_world endpoint")
    # Execute the service and charge the user 0.000_001 USDC
    print("Preparing response with 0.000001 USDC charge")
    response = JSONResponse(
        content={"message": "Hello from Agentopia!"}, headers={"X-Usdc-Used": "1"}
    )
    print("Returning response")
    return response
```

Checkout the repo: [Hello World Service](https://github.com/nurturelabs-co/agentopia-hello-world)

### Open Router Service
For more flexibility, you can use the Agentopia client to charge the user according to your app's dynamic requirements.
```python
import json
import os

import httpx
import requests
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse, StreamingResponse
from agentopia import Agentopia  # type: ignore

app = FastAPI()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
if not OPENROUTER_API_KEY:
    raise Exception("OPENROUTER_API_KEY environment variable not set")


@app.post("/chat/completions")
async def chat_completions(request: Request):
    print("Starting payable stream wrapper")
    # Get hold ID from header
    x_hold_id = request.headers.get("X-Hold-Id")

    if x_hold_id is None:
        print("No hold ID provided, raising 402 error")
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="A Agentopia `X-Hold-Id` header is required",
        )

    print(f"Received hold ID: {x_hold_id}")

    # Create client instance
    print("Creating Agentopia client")
    agentopia_client = Agentopia()

    # Verify hold using hold manager
    print(f"Verifying hold {x_hold_id}")
    try:
        x_hold = agentopia_client.hold.get(x_hold_id)
        print(f"Hold verification successful: {x_hold}")
    except requests.exceptions.HTTPError:
        print("Hold verification failed")
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="Invalid hold ID",
        )

    try:
        # Get the request body
        body = await request.json()

        # Forward the request to OpenRouter
        async with httpx.AsyncClient() as client:
            headers = {
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "HTTP-Referer": "https://agentopia.xyz",
                "X-Title": "Agentopia LLM Service",
            }

            # If streaming is enabled, stream the response
            if body.get("stream", False):
                response = await client.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    json=body,
                    headers=headers,
                    follow_redirects=True,
                    timeout=30.0,
                )

                async def generate():
                    try:
                        async for line in response.aiter_lines():
                            if line:
                                # Skip empty lines and "OPENROUTER PROCESSING" messages
                                if (
                                    line.strip() == ""
                                    or "OPENROUTER PROCESSING" in line
                                ):
                                    continue

                                # Handle data: prefix
                                if line.startswith("data: "):
                                    line = line[6:]  # Remove "data: " prefix

                                try:
                                    parsed_line = json.loads(line)
                                    if "error" in parsed_line:
                                        raise HTTPException(
                                            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                            detail=parsed_line["error"],
                                        )
                                    # Add back the "data: " prefix for SSE format
                                    yield f"data: {json.dumps(parsed_line)}\n\n"
                                except json.JSONDecodeError:
                                    print(f"JSONDecodeError on line: {line}")
                                    continue

                        yield "data: [DONE]\n\n"
                    finally:
                        # Release hold and charge user using hold manager
                        print(f"Releasing hold {x_hold_id} with amount 1000")
                        try:
                            agentopia_client.hold.release(hold_id=x_hold_id, amount=1000)
                            print("Hold released successfully")
                        except requests.exceptions.HTTPError:
                            print("Failed to release hold")
                            raise HTTPException(
                                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail="Failed to process payment",
                            )

                return StreamingResponse(
                    generate(),
                    media_type="text/event-stream",
                    headers={
                        "Content-Type": "text/event-stream",
                        "Cache-Control": "no-cache",
                        "Connection": "keep-alive",
                        "X-Usdc-Used": "1000",
                    },
                )

            # For non-streaming requests
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                json=body,
                headers=headers,
            )

            # Release hold and charge user
            try:
                agentopia_client.hold.release(hold_id=x_hold_id, amount=1000)
                print("Hold released successfully")
            except requests.exceptions.HTTPError:
                print("Failed to release hold")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to process payment",
                )

            return JSONResponse(
                content=response.json(), headers={"X-Usdc-Used": "1000"}
            )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )

```

<!-- Checkout the repo: [Open Router Service](https://github.com/nurturelabs-co/agentopia-openrouter) -->

### Register your service

You need to register your service on Agentopia Marketplace to make it available for users to use.

```python
from agentopia import Agentopia, AgentopiaServiceModel
agentopia_client = Agentopia(private_key="your_private_key")

service: AgentopiaServiceModel = agentopia_client.service.register(
    name="Hello World",
    description="A simple hello world service",
    base_url="http://api.hello.world",
    slug="hello-world-1234",
    initial_hold_amount=100000,  # $0.1 USDC
    initial_hold_expires_in=3600,  # 1 hour
    api_schema_url="http://api.hello.world/openapi.json",
)
```

### Withdraw earnings from Agentopia Wallet

#### Get your balance

```python
from agentopia import Agentopia
agentopia_client = Agentopia(private_key="your_private_key")
balance = agentopia_client.get_balance()
```

#### Withdraw your balance

```python
from agentopia import Agentopia
agentopia_client = Agentopia(private_key="your_private_key")
agentopia_client.withdraw(amount=100000)
```

This will initiate a withdrawal request which will be processed in a few minutes on the base blockchain.

## Contact Us

If you have any questions or feedback, please contact us at 

- [Telegram](https://t.me/yashdotagarwal)
- [Twitter](https://x.com/yashdotagarwal)
- [Email](mailto:yash@nurturelabs.co)   
