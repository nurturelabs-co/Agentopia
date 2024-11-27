from typing import List

from pydantic import BaseModel


class APIKey(BaseModel):
    key: str
    name: str


class APIKeyManager:
    """API key management for Agentopia"""

    def __init__(self, client):
        self.client = client

    def create(self, name: str) -> APIKey:
        """Create a new API key.

        Args:
            name: Name/description for the API key

        Returns:
            API key details including the key string
        """
        response = self.client._post(
            f"/v1/user/{self.client.address}/api-key", params={"key_name": name}
        )
        return APIKey(**response)

    def list(self, skip: int = 0, limit: int = 10) -> List[APIKey]:
        """List API keys.

        Args:
            skip: Number of records to skip for pagination
            limit: Maximum number of records to return

        Returns:
            List of API keys
        """
        response = self.client._get(
            f"/v1/user/{self.client.address}/api-key",
            params={"skip": skip, "limit": limit},
        )
        return [APIKey(**item) for item in response["items"]]

    def deactivate(self, api_key: str) -> bool:
        """Deactivate an API key.

        Args:
            api_key: The API key string to deactivate

        Returns:
            The deactivated API key
        """
        response = self.client._delete(
            f"/v1/user/{self.client.address}/api-key/{api_key}"
        )
        if response.get("message") == "API key deactivated":
            return True
        return False
