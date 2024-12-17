# Register Your Service

This guide explains how to register your service with Agentopia, making it available for users and AI agents to discover and use.

## Prerequisites

1. A working API service with Agentopia integration
2. Agentopia SDK installed (`pip install agentopia`)
3. Your service provider private key

## Registration Process

### 1. Initialize Agentopia Client

```python
from agentopia import Agentopia

client = Agentopia(private_key="your-private-key")
```

### 2. Define Service Configuration

Create a `ServiceConfig` object that defines your service:

```python
from schema import ServiceConfig

service_config = ServiceConfig(
    name="Your Service Name",
    description="Clear description of what your service does",
    slug="your-service-slug",
    default_hold_amount=100000,  # Default hold in micro USDC
    default_hold_expires_in=3600,  # Default hold duration in seconds
    logo_url="https://your-logo-url.com/logo.png",
)
```

### 3. Register the Service

There are two ways to register your service:

#### Option 1: Automatic Registration

If you're using FastAPI with Agentopia's service mounting:

```python
from fastapi import FastAPI
app = FastAPI()

# Your service will be automatically registered
# when mounted in the Agentopia service manager
```

#### Option 2: Manual Registration

For manual registration or other frameworks:

```python
service = client.service.register(
    name=service_config.name,
    description=service_config.description,
    base_url="https://api.your-service.com",
    slug=service_config.slug,
    default_hold_amount=service_config.default_hold_amount,
    default_hold_expires_in=service_config.default_hold_expires_in,
    api_schema=your_api_schema,  # OpenAPI schema
    logo_url=service_config.logo_url
)
```

## Service Configuration Details

### Required Fields

- `name`: Display name for your service
- `description`: Clear explanation of functionality
- `slug`: Unique identifier (URL-friendly)
- `default_hold_amount`: Default amount to hold in micro USDC
- `default_hold_expires_in`: Default hold duration in seconds
- `base_url`: Your service's base URL
- `api_schema`: OpenAPI/Swagger schema

### Optional Fields

- `logo_url`: URL to your service's logo
- `contact_info`: Contact details for support
- `legal_info`: License and legal information

## Updating Your Service

To update an existing service:

```python
client.service.update(
    slug="your-service-slug",
    name="Updated Name",
    description="Updated description",
    base_url="https://new-url.com",
    default_hold_amount=200000,  # Updated hold amount
    default_hold_expires_in=7200,  # Updated expiration
    api_schema=updated_schema,
    logo_url="https://new-logo-url.com/logo.png",
    is_public=True
)
```

## Best Practices

1. **Service Description**
   - Be clear and concise
   - List key features
   - Specify any requirements
   - Include usage examples

2. **Hold Configuration**
   - Set reasonable default holds
   - Consider your service's pricing model
   - Account for processing time in expiration

3. **API Schema**
   - Keep OpenAPI schema up-to-date
   - Document all endpoints clearly
   - Include request/response examples

4. **Monitoring**
   - Track service usage
   - Monitor hold patterns
   - Update configuration based on usage

## Example: Complete Registration

Here's a complete example including error handling:

```python
from agentopia import Agentopia
from schema import ServiceConfig
import requests

try:
    # Initialize client
    client = Agentopia(private_key="your-private-key")
    
    # Define configuration
    config = ServiceConfig(
        name="Image Processing API",
        description="AI-powered image processing and analysis",
        slug="image-processor",
        default_hold_amount=500000,  # 0.5 USDC
        default_hold_expires_in=3600,
        logo_url="https://example.com/logo.png"
    )
    
    # Register service
    service = client.service.register(
        name=config.name,
        description=config.description,
        base_url="https://api.your-service.com",
        slug=config.slug,
        default_hold_amount=config.default_hold_amount,
        default_hold_expires_in=config.default_hold_expires_in,
        api_schema=app.openapi(),
        logo_url=config.logo_url
    )
    
    # Make service public
    client.service.update(
        slug=config.slug,
        is_public=True
    )
    
    print(f"Service registered successfully: {service.id}")

except requests.exceptions.HTTPError as e:
    print(f"HTTP Error during registration: {e}")
except Exception as e:
    print(f"Error registering service: {e}")
```

## After Registration

1. Test your service thoroughly
2. Monitor service health
3. Update documentation as needed
4. Engage with users for feedback
5. Monitor usage metrics

Your service is now ready to be discovered and used by the Agentopia community!
