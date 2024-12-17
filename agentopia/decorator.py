import logging
from functools import wraps
from typing import Callable

import requests
from fastapi import HTTPException, status

from agentopia.client import Agentopia
from agentopia.settings import settings


def payable(hold_amount: int, hold_expires_in: int = 3600):
    """
    Decorator to make an endpoint require payment via Agentopia hold system.

    Args:
        hold_amount: Amount to hold in USDC (6 decimals)
        hold_expires_in: Hold expiration time in seconds (default 1 hour)
    """

    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            logging.debug("Starting payable decorator wrapper")

            if settings.AGENTOPIA_LOCAL_MODE:
                logging.debug("Local model enabled, bypassing hold verification")
                response = await func(*args, **kwargs)
                return response

            # Get hold ID from header
            request = kwargs.get("request", None)
            x_hold_id = (
                request.headers.get("X-Hold-Id")
                or kwargs.get("x-hold-id")
                or kwargs.get("x_hold_id")
            )

            if x_hold_id is None:
                logging.warning("No hold ID provided, raising 402 error")
                raise HTTPException(
                    status_code=status.HTTP_402_PAYMENT_REQUIRED,
                    detail="A Agentopia `X-Hold-Id` header is required",
                )

            logging.debug(f"Received hold ID: {x_hold_id}")

            # Create client instance
            logging.debug("Creating Agentopia client")
            client = Agentopia()

            # Verify hold using hold manager
            logging.debug(f"Verifying hold {x_hold_id}")
            try:
                x_hold = client.hold.get(x_hold_id)
                logging.debug(f"Hold verification successful: {x_hold}")
            except requests.exceptions.HTTPError:
                logging.error("Hold verification failed")
                raise HTTPException(
                    status_code=status.HTTP_402_PAYMENT_REQUIRED,
                    detail="Invalid hold ID",
                )

            # Execute the actual endpoint
            logging.debug("Executing wrapped endpoint")
            response = await func(*args, **kwargs)

            # Get amount used from headers if JSONResponse, otherwise default to 1
            amount_used = 1
            if hasattr(response, "headers"):
                # Add CORS expose header to make X-Usdc-Used visible to client
                response.headers["Access-Control-Expose-Headers"] = "X-Usdc-Used"
                if "X-Usdc-Used" in response.headers:
                    amount_used = int(response.headers["X-Usdc-Used"])
            logging.debug(f"Amount used: {amount_used}")

            # Release hold and charge user using hold manager
            logging.debug(f"Releasing hold {x_hold_id} with amount {amount_used}")
            try:
                client.hold.release(hold_id=x_hold_id, amount=amount_used)
                logging.debug("Hold released successfully")
            except requests.exceptions.HTTPError:
                logging.error("Failed to release hold")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to process payment",
                )

            logging.debug("Returning response")
            logging.debug(f"Response headers in hello world: {response.headers}")
            return response

        # Add OpenAPI metadata for hold amount
        wrapper.__dict__["openapi_extra"] = {"x-hold-amount": str(hold_amount)}

        return wrapper

    return decorator
