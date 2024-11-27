from decimal import Decimal
from typing import Dict, List, Optional, Union
from uuid import UUID

import httpx
from pydantic import BaseModel

from agentopia.utility import USDCAmount, Web3Address


class ServiceModel(BaseModel):
    """Pydantic model for Service"""

    id: UUID
    name: str
    description: str
    base_url: str
    slug: str
    default_hold_amount: USDCAmount
    default_hold_expires_in: int
    app_url: Optional[str] = None
    logo_url: Optional[str] = None
    readme_url: Optional[str] = None
    api_schema_url: Optional[str] = None
    is_active: bool = True
    service_provider_id: Web3Address
    is_public: bool = False


class ServiceManager:
    """Service management for Agentopia"""

    def __init__(self, client):
        self.client = client

    def execute_via_proxy(
        self, service_slug: str, endpoint_path: str, method: str
    ) -> Dict:
        """Execute a service by calling its endpoint through the Agentopia proxy.

        Args:
            service_slug: The unique identifier for the service
            endpoint_path: The path of the endpoint to call
            method: HTTP method to use (GET or POST)

        Returns:
            The response from the service endpoint
        """
        # Call the execute endpoint with the appropriate method
        # get the hold amount and hold expires in from the service
        # service = self.get_by_slug(service_slug)
        # hold_amount = service.default_hold_amount
        # hold_expires_in = service.default_hold_expires_in

        # # create a hold
        # hold_id = self.client.hold.create(
        #     service.id, int(Decimal(str(hold_amount))), hold_expires_in
        # )

        # Set header with hold ID
        # headers = {"X-Hold-Id": str(hold_id)}

        # execute the service
        if method.upper() == "GET":
            return self.client._get(
                f"/v1/execute/service/{service_slug}/{endpoint_path}"
            )
        elif method.upper() == "POST":
            return self.client._post(
                f"/v1/execute/service/{service_slug}/{endpoint_path}"
            )
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")

    def execute(
        self, service_slug: str, endpoint_path: str, method: str, **kwargs
    ) -> Dict:
        """Execute a service by calling its endpoint through the Agentopia proxy.

        Args:
            service_slug: The unique identifier for the service
            endpoint_path: The path of the endpoint to call
            method: HTTP method to use (GET or POST)
            **kwargs: Additional arguments to pass to the request (e.g. json, params)

        Returns:
            The response from the service endpoint
        """
        # Call the execute endpoint with the appropriate method
        # get the hold amount and hold expires in from the service
        service: ServiceModel = self.get_by_slug(service_slug)
        hold_amount = service.default_hold_amount
        hold_expires_in = service.default_hold_expires_in

        # create a hold
        hold_id = self.client.hold.create(
            service.id, int(Decimal(str(hold_amount))), hold_expires_in
        )

        # Set header with hold ID
        headers = {"X-Hold-Id": str(hold_id)}
        if "headers" in kwargs:
            headers.update(kwargs["headers"])
            del kwargs["headers"]

        endpoint_path = (
            endpoint_path if endpoint_path.startswith("/") else f"/{endpoint_path}"
        )
        # execute the service by calling base URL directly
        if method.upper() == "GET":
            with httpx.Client() as client:
                response = client.get(
                    f"{service.base_url}{endpoint_path}", headers=headers, **kwargs
                )
                response.raise_for_status()
                return response.json()

        elif method.upper() == "POST":
            with httpx.Client() as client:
                response = client.post(
                    f"{service.base_url}{endpoint_path}", headers=headers, **kwargs
                )
                response.raise_for_status()
                return response.json()

        else:
            raise ValueError(f"Unsupported HTTP method: {method}")

    def register(
        self,
        name: str,
        description: str,
        base_url: str,
        slug: str,
        initial_hold_amount: Union[Decimal, int],
        initial_hold_expires_in: int,
        app_url: Optional[str] = None,
        logo_url: Optional[str] = None,
        readme_url: Optional[str] = None,
        api_schema_url: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> ServiceModel:
        """Create a new service.

        Args:
            name: Name of the service
            description: Description of what the service does
            base_url: Base URL where the service is hosted
            slug: URL-friendly identifier for the service
            initial_hold_amount: Default amount to hold for service calls in USDC (6 decimals)
            initial_hold_expires_in: Default hold expiration time in seconds
            app_url: Optional URL to the service's web application
            logo_url: Optional URL to the service's logo
            readme_url: Optional URL to the service's documentation
            api_schema_url: Optional URL to the service's OpenAPI schema
            tags: Optional list of tags to categorize the service

        Returns:
            Created service details as a Service object
        """
        data = {
            "service": {
                "name": name,
                "description": description,
                "base_url": base_url,
                "slug": slug,
                "initial_hold_amount": initial_hold_amount,
                "initial_hold_expires_in": initial_hold_expires_in,
                "app_url": app_url,
                "logo_url": logo_url,
                "readme_url": readme_url,
                "api_schema_url": api_schema_url,
            },
            "tags": tags,
        }

        response = self.client._post("/v1/service", json=data)
        return ServiceModel(**response)

    def update(
        self,
        slug: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        base_url: Optional[str] = None,
        initial_hold_amount: Optional[Decimal] = None,
        initial_hold_expires_in: Optional[int] = None,
        is_active: Optional[bool] = None,
        app_url: Optional[str] = None,
        logo_url: Optional[str] = None,
        readme_url: Optional[str] = None,
        api_schema_url: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> Dict:
        """Update an existing service.

        Args:
            slug: Service slug to update
            name: Optional new name
            description: Optional new description
            base_url: Optional new base URL
            initial_hold_amount: Optional new default hold amount in USDC (6 decimals)
            initial_hold_expires_in: Optional new default hold expiration in seconds
            is_active: Optional new active status
            app_url: Optional new app URL
            logo_url: Optional new logo URL
            readme_url: Optional new readme URL
            api_schema_url: Optional new API schema URL
            tags: Optional new tags list

        Returns:
            Updated service details
        """
        data = {}
        if name is not None:
            data["service"]["name"] = name
        if description is not None:
            data["service"]["description"] = description
        if base_url is not None:
            data["service"]["base_url"] = base_url
        if initial_hold_amount is not None:
            data["service"]["initial_hold_amount"] = initial_hold_amount
        if initial_hold_expires_in is not None:
            data["service"]["initial_hold_expires_in"] = initial_hold_expires_in
        if is_active is not None:
            data["service"]["is_active"] = is_active
        if app_url is not None:
            data["service"]["app_url"] = app_url
        if logo_url is not None:
            data["service"]["logo_url"] = logo_url
        if readme_url is not None:
            data["service"]["readme_url"] = readme_url
        if api_schema_url is not None:
            data["service"]["api_schema_url"] = api_schema_url
        if tags is not None:
            data["tags"] = tags

        return self.client._put(f"/v1/service/{slug}", json=data)

    def update_path(
        self,
        slug: str,
        path: str,
        method: str,
        hold_amount: Optional[Decimal] = None,
        hold_expires_in: Optional[int] = None,
    ) -> Dict:
        """Update service path configuration.

        Args:
            slug: Service slug
            path: API path to update
            method: HTTP method (GET, POST, etc)
            hold_amount: Optional new hold amount for this path in USDC (6 decimals)
            hold_expires_in: Optional new hold expiration time in seconds

        Returns:
            Updated path details
        """
        data = {}
        if hold_amount is not None:
            data["service_path"]["hold_amount"] = hold_amount
        if hold_expires_in is not None:
            data["service_path"]["hold_expires_in"] = hold_expires_in

        return self.client._put(
            f"/v1/service/{slug}/path/{path}?method={method}", json=data
        )

    def get_by_slug(self, slug: str) -> ServiceModel:
        """Get service details by slug.

        Args:
            slug: Service slug identifier

        Returns:
            Service details as ServiceModel
        """
        response = self.client._get(f"/v1/service/slug/{slug}")
        return ServiceModel(**response)

    def get(self, service_id: UUID) -> ServiceModel:
        """Get service details by ID.

        Args:
            service_id: Service UUID

        Returns:
            Service details as ServiceModel
        """
        response = self.client._get(f"/v1/service/{service_id}")
        return ServiceModel(**response)

    def search(self, query: str, limit: int = 10) -> List[ServiceModel]:
        """Search for services.

        Args:
            query: Search query string
            limit: Maximum number of results to return (default: 10, max 10)

        Returns:
            List of matching service details as ServiceModel
        """
        response = self.client._get(
            "/v1/service/search", params={"query": query, "limit": min(limit, 10)}
        )
        return [ServiceModel(**service) for service in response]
