# Searching for Services

Before using a service through Agentopia, you'll need to find the appropriate service for your needs. Agentopia provides search functionality to help you discover services.

## Using the Python SDK

### Basic Service Search

Use the `search()` method to find services based on natural language queries:

=== "Python SDK"
    ```python
    from agentopia import Agentopia
    
    # Initialize client
    agentopia = Agentopia(private_key="your_private_key")
    
    # Search for services
    services = agentopia.service.search(
        query="twitter data analysis",  # Natural language search query
        limit=5                         # Maximum number of results (default: 10, max: 10)
    )
    
    # Print search results
    for service in services:
        print(f"Name: {service.name}")
        print(f"Description: {service.description}")
        print(f"Slug: {service.slug}")
        print(f"Tags: {service.tags}")
        print("---")
    ```

### Service Details

Once you find a service you want to use, you can get its full details using the slug:

=== "Python SDK"
    ```python
    # Get service details by slug
    service = agentopia.service.get_by_slug("service-slug")
    
    print(f"Service Name: {service.name}")
    print(f"Description: {service.description}")
    print(f"Default Hold Amount: {service.default_hold_amount} USDC")
    print(f"Hold Expiration: {service.default_hold_expires_in} seconds")
    ```

## Service Information

Each service includes the following key information:

- `name`: The service name
- `description`: Detailed description of what the service does
- `slug`: Unique identifier used to reference the service
- `tags`: Categories or keywords associated with the service
- `default_hold_amount`: Default amount held for service calls (in USDC)
- `default_hold_expires_in`: Default hold expiration time in seconds
- `app_url`: Optional URL to the service's web application
- `readme_url`: Optional URL to the service's documentation
- `api_schema`: Optional OpenAPI schema defining the service endpoints

## Next Steps

Once you've found a service you want to use, refer to [Using Services via Proxy API](run-proxy-api.md) for instructions on how to make API calls to the service.
