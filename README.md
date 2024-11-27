# Agentopia

- Add superpowers to your AI agent. Our SDK empowers AI agents to discover and pay for services, products, and other agents on demand—seamlessly and autonomously.
- Devs, you can easily:
  - Add new capabilities to your AI agent 10x faster. Discover and pay for services, APIs, data set or infra your AI agent needs. 100% automated, no credit cards or bank account needed
  - Sell your products & services to AI agents. Build and monetise your own service or remix the existing ones to build new ones and start earning instantly. No permissions required.

## Install the SDK

```bash
pip install agentopia
```

## Do want to sell your service?

You can build a API/Data service and sell it on Agentopia Marketplace where users/AI Agents can pay for your service on per use basis with USDC on the base blockchain.

### Build a service and sell it on Agentopia Marketplace.

#### Hello World Service

=== "Using Python SDK"
    ```python
    from fastapi import FastAPI, Request
    from fastapi.responses import JSONResponse
    from agentopia import payable

    app = FastAPI()

    @app.get("/hello_world")
    @payable(
        hold_amount=100000, hold_expires_in=3600
    )  # Hold $0.1 in the users account for 1hr
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

Github link to this repo is here: [Hello World Service](https://github.com/nurturelabs-co/example_agentopia_services/tree/main/hello_world)

#### Open Router Service

=== "Using Python SDK"
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

Github link to this repo is here: [Open Router Service](https://github.com/nurturelabs-co/example_agentopia_services/tree/main/llm_service)

### Register your service

You need to register your service on Agentopia Marketplace to make it available for users to use.

=== "Using Python SDK"
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

### Withdraw your earnings from your Agentopia Wallet

#### Get your balance

=== "Using Python SDK"
    ```python
    from agentopia import Agentopia
    agentopia_client = Agentopia(private_key="your_private_key")
    balance = agentopia_client.get_balance()
    ```

#### Withdraw your balance

=== "Using Python SDK"
    ```python
    from agentopia import Agentopia
    agentopia_client = Agentopia(private_key="your_private_key")
    agentopia_client.withdraw(amount=100000)
    ```

This will initiate a withdrawal request which will be processed in a few minutes on the base blockchain.

## Do want to use a service?

Search and use services on Agentopia Marketplace.

### Fund your Agentopia Wallet

=== "Using Python SDK"
    ```python
    from agentopia import Agentopia
    agentopia_client = Agentopia(private_key="your_private_key")
    agentopia_client.deposit(amount=1000_000)
    ```

This will initiate a deposit of 1 USDC (the values used in the SDK are in micro USDC) request which will be processed in a few minutes on the base blockchain.

### Use a service

=== "Using Python SDK"
    ```python
    from agentopia import Agentopia
    agentopia_client = Agentopia(private_key="your_private_key")
    response = agentopia_client.service.execute_via_proxy(
        service_slug="hello-world-1234", endpoint_path="hello_world", method="GET"
    )
    print(response)
    ```

## Contact Us

If you have any questions or feedback, please contact us at 

- [Telegram](https://t.me/yashdotagarwal)
- [Twitter](https://x.com/yashdotagarwal)
- [Email](mailto:yash@nurturelabs.co)   
