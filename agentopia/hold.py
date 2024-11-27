from typing import Dict, Optional
from uuid import UUID

from agentopia.utility import dump_json


class HoldManager:
    """Hold management for Agentopia"""

    def __init__(self, client):
        self.client = client

    def create(self, service_id: UUID, amount: int, expires_in: int = 300) -> UUID:
        """Create a new hold.

        Args:
            service_id: ID of the service to create hold for
            amount: Amount to hold in USDC (6 decimals)
            expires_in: Hold expiration time in seconds (default: 300)

        Returns:
            Hold ID
        """
        response = self.client._post(
            "/v1/hold",
            json={"service_id": service_id, "amount": amount, "expires_in": expires_in},
        )
        return response["hold_id"]

    def get(self, hold_id: UUID) -> Dict:
        """Get details of a specific hold.

        Args:
            hold_id: UUID of the hold to retrieve

        Returns:
            Hold details
        """
        return self.client._get(f"/v1/hold/{hold_id}")

    def release(
        self,
        hold_id: UUID,
        amount: int,
        input_json: Optional[Dict] = None,
        result_json: Optional[Dict] = None,
    ) -> Dict:
        """Release a hold and charge the specified amount.

        Args:
            hold_id: UUID of the hold to release
            amount: Amount to charge from the hold in USDC (6 decimals)
            input_json: Optional input data to store with transaction
            result_json: Optional result data to store with transaction

        Returns:
            Response indicating success
        """
        return self.client._delete(
            f"/v1/hold/{hold_id}",
            json={
                "amount": amount,
                "input_json": dump_json(input_json) if input_json else None,
                "result_json": dump_json(result_json) if result_json else None,
            },
        )

    def split(self, hold_id: UUID, split_details: list[Dict]) -> Dict:
        """Split an existing hold into multiple new holds.

        Args:
            hold_id: UUID of the hold to split
            split_details: List of dicts containing service_id and amount for each new hold

        Returns:
            Dict containing original hold and new holds
        """
        return self.client._post(f"/v1/hold/{hold_id}/split", json=split_details)
