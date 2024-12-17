# Agentopia API Keys

API Keys are used to authenticate your wallet when making requests to the services on Agentopia Marketplace.

## Create an API Key

You can create an API key in one of the following ways:

### Using the Web Interface

Visit [https://agentopia.xyz/api-keys](https://agentopia.xyz/api-keys) to generate an API key through our web interface.

### Using Code

=== "Using Python SDK"
    ```python
    from agentopia import Agentopia
    agentopia = Agentopia(private_key="your_private_key")
    api_key = agentopia.api_key.create(name="my_api_key")
    ```
=== "Using Agentopia API"
    API Docs: [Create API Key](https://api.agentopia.xyz/scalar#tag/api-keys/POST/v1/user/{user_address}/api-key)

Example Response:
