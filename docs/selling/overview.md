# Selling via Agentopia: Overview

Agentopia is a decentralized marketplace that enables developers to monetize their APIs and services by integrating them into the Agentopia ecosystem. With built-in payment processing using USDC (USD Coin), usage tracking, and automatic service discovery, Agentopia makes it simple to start earning from your APIs.

## Why Choose Agentopia?

### For Developers
- **Instant Monetization**: Start earning immediately with per-request pricing in USDC
- **Flexible Integration**: Use your preferred API framework with our SDK
- **Automated Payments**: Built-in hold system ensures fair compensation
- **Usage Analytics**: Track service usage and earnings in real-time
- **AI-Ready**: Your services become instantly accessible to AI agents

### For Users
- **Pay-per-Use**: Only pay for what you consume
- **Transparent Pricing**: Clear cost structure with no hidden fees
- **Secure Transactions**: Built on blockchain technology
- **Service Discovery**: Easy access to a growing ecosystem of APIs

## How It Works

1. **Integration**
   - Add Agentopia SDK to your API
   - Configure pricing and holds
   - Define service metadata

2. **Registration**
   - Register your service with Agentopia
   - Provide OpenAPI documentation
   - Set default hold parameters

3. **Deployment**
   - Deploy your service
   - Agentopia handles discovery
   - Monitor usage and earnings

## Quick Start Example

Here's a minimal example of an Agentopia-enabled endpoint:

```python
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from agentopia import payable

app = FastAPI()

@app.get("/hello_world")
@payable(
    hold_amount=100000,  # Hold 0.1 USDC
    hold_expires_in=3600  # Hold for 1 hour
)
async def hello_world(request: Request):
    # Your service logic here
    return JSONResponse(
        content={"message": "Hello from Agentopia!"},
        headers={"X-Usdc-Used": "1"}  # Charge 0.000001 USDC
    )
```

## Key Concepts

### 1. Holds
- Temporary fund reservations
- Ensures available balance
- Flexible consumption
- Automatic expiration

### 2. Pricing
- Per-request charging
- Dynamic pricing support
- Micro-transaction capable
- Automatic settlement

### 3. Service Management
- Automatic registration
- Version control
- Usage statistics
- Performance monitoring

## Integration Steps

1. **Setup**
   ```bash
   pip install agentopia
   ```

2. **Configuration**
   ```python
   from schema import ServiceConfig
   
   config = ServiceConfig(
       name="Your Service",
       description="Service description",
       slug="your-service",
       default_hold_amount=100000,
       default_hold_expires_in=3600
   )
   ```

3. **Implementation**
   - Add `@payable` decorator to endpoints
   - Configure hold amounts
   - Set charge amounts

4. **Registration**
   - Register with Agentopia
   - Configure service details
   - Set pricing parameters

## Best Practices

1. **Pricing Strategy**
   - Set competitive rates
   - Consider operational costs
   - Plan for scaling

2. **Hold Management**
   - Appropriate hold amounts
   - Reasonable expiration times
   - Error handling

3. **Documentation**
   - Clear API documentation
   - Usage examples
   - Pricing transparency

4. **Monitoring**
   - Track usage patterns
   - Monitor performance
   - Analyze user behavior

## Advanced Features

### Dynamic Pricing
```python
@app.post("/process")
@payable(hold_amount=1000000)  # Hold 1 USDC
async def process(request: Request, data: dict):
    # Calculate cost based on processing
    cost = calculate_processing_cost(data)
    result = process_data(data)
    
    return JSONResponse(
        content={"result": result},
        headers={"X-Usdc-Used": str(cost)}
    )
```

### Batch Processing
```python
@app.post("/batch")
@payable(
    hold_amount=5000000,  # Hold 5 USDC
    hold_expires_in=7200  # 2 hours
)
async def batch_process(request: Request, items: List[dict]):
    total_cost = 0
    results = []
    
    for item in items:
        cost = process_item(item)
        total_cost += cost
        results.append({"item": item, "cost": cost})
    
    return JSONResponse(
        content={"results": results},
        headers={"X-Usdc-Used": str(total_cost)}
    )
```

## Next Steps

1. [Set up your first service](hello-world-service.md)
2. [Learn about the service decorator](service-decorator.md)
3. [Understand hold management](handle-holds.md)
4. [Register your service](register-service.md)

Join the Agentopia ecosystem today and start monetizing your APIs with ease!
