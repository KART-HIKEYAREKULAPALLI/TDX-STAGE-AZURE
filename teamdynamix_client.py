import aiohttp
import asyncio
from datetime import datetime

class TeamDynamixClient:
    """Manages interactions with the TeamDynamix API."""
    
    def __init__(self, token_manager):
        """
        Initialize the TeamDynamixClient with hardcoded parameters.
        
        Args:
            token_manager: Instance of TokenManager for authentication.
        """
        self.token_manager = token_manager
        self.base_url = "https://servicecenter.midlandhealth.org/TDWebApi/api"
        self.appid_tickets = 156
        self.appid_assets = 157
        self.appid_kbase = 357
        self.appid_service = 357

    async def search_tickets(
        self,
        date: datetime,
        ResponsibleGroupID: int = None,
        RequestorUid: str = None,
        rate_limit_delay: float = 2.0
    ) -> list:
        """
        Searches tickets modified on a specific date from 00:00 to 23:59 (24-hour cycle),
        filtered by responsible group or requestor. Date is mandatory.

        Args:
            date (datetime): Date for ticket search (e.g., datetime(2025, 1, 15)).
            ResponsibleGroupID (int, optional): ID of the responsible group.
            RequestorUid (str, optional): UID of the requestor.
            rate_limit_delay (float): Delay in seconds to respect rate limits (30 calls/60s).

        Returns:
            list: List of ticket dictionaries.

        Raises:
            ValueError: If date is not provided when ResponsibleGroupID is specified.
        """
        # Initialize semaphore for concurrency control
        semaphore = asyncio.Semaphore(55)  # Limit to 55 concurrent requests

        # Validate date parameter
        if date is None and ResponsibleGroupID is not None:
            raise ValueError("Date is mandatory when searching by ResponsibleGroupID")

        # Initialize ticket list
        tickets = []

        # Set headers for API requests
        headers = {
            "Authorization": f"Bearer {await self.token_manager.get_access_token()}",
            "Content-Type": "application/json; charset=utf-8"
        }

        async with semaphore:
            # Define the start and end of the day (00:00 to 23:59)
            start_time = date.replace(hour=0, minute=0, second=0, microsecond=0)
            end_time = date.replace(hour=23, minute=59, second=59, microsecond=999999)

            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/{self.appid_tickets}/tickets/search"
                params = {
                    "ModifiedDateFrom": start_time.strftime("%Y-%m-%dT%H:%M:%S"),
                    "ModifiedDateTo": end_time.strftime("%Y-%m-%dT%H:%M:%S"),
                    "OrderBy": "ModifiedDate DESC"
                }
                # Add optional filters if provided
                if ResponsibleGroupID is not None:
                    params["ResponsibleGroupID"] = str(ResponsibleGroupID)
                if RequestorUid is not None:
                    params["RequestorUid"] = str(RequestorUid)

                try:
                    async with session.post(url, headers=headers, json=params) as response:
                        if response.status != 200:
                            raise Exception(f"Failed to search tickets: {response.status}")
                        tickets = await response.json()
                except Exception:
                    pass  # Skip errors to continue processing
                await asyncio.sleep(rate_limit_delay)  # Respect rate limit (30 calls/60s)

        return tickets

    async def get_ticket_details(self, ticket_id: int, app_id: int = 156) -> dict:
        """
        Retrieves detailed information for a specific ticket using GET /api/{appId}/tickets/{id}.

        Args:
            ticket_id (int): ID of the ticket.
            app_id (int): Application ID for the ticket (default: 156).

        Returns:
            dict: Ticket details as a TeamDynamix.Api.Tickets.Ticket object.

        Raises:
            Exception: If the API request fails.
        """
        semaphore = asyncio.Semaphore(55)  # Limit to 55 concurrent requests
        async with semaphore:
            headers = {
                "Authorization": f"Bearer {await self.token_manager.get_access_token()}",
                "Content-Type": "application/json; charset=utf-8"
            }
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/{app_id}/tickets/{ticket_id}"
                try:
                    async with session.get(url, headers=headers) as response:
                        if response.status != 200:
                            raise Exception(f"Failed to get ticket {ticket_id}: {response.status}")
                        return await response.json()
                except Exception:
                    raise
                finally:
                    await asyncio.sleep(2.0)  # Respect rate limit (60 calls/60s)

    async def get_ticket_feed(self, ticket_id: int, app_id: int = 156) -> list:
        """
        Retrieves feed entries for a specific ticket using GET /api/{appId}/tickets/{id}/feed.

        Args:
            ticket_id (int): ID of the ticket.
            app_id (int): Application ID for the ticket (default: 156).

        Returns:
            list: List of feed entries as TeamDynamix.Api.Feed.ItemUpdate objects.

        Raises:
            ValueError: If the response is not a list.
            Exception: If the API request fails.
        """
        semaphore = asyncio.Semaphore(55)  # Limit to 55 concurrent requests
        async with semaphore:
            headers = {
                "Authorization": f"Bearer {await self.token_manager.get_access_token()}",
                "Content-Type": "application/json; charset=utf-8"
            }
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/{app_id}/tickets/{ticket_id}/feed"
                try:
                    async with session.get(url, headers=headers) as response:
                        if response.status != 200:
                            raise Exception(f"Failed to get feed for ticket {ticket_id}: {response.status}")
                        feed_data = await response.json()
                        if not isinstance(feed_data, list):
                            raise ValueError("Expected a list of feed entries")
                        return feed_data
                except Exception:
                    raise
                finally:
                    await asyncio.sleep(2.0)  # Respect rate limit (60 calls/60s)

    async def get_ticket_assets(self, ticket_id: int, app_id: int = 157) -> list:
        """
        Retrieves assets associated with a specific ticket using GET /api/{appId}/tickets/{id}/assets.

        Args:
            ticket_id (int): ID of the ticket.
            app_id (int): Application ID for the ticket (default: 157).

        Returns:
            list: List of configuration items as TeamDynamix.Api.Cmdb.ConfigurationItem objects.

        Raises:
            ValueError: If the response is not a list or items are not dictionaries.
            Exception: If the API request fails.
        """
        semaphore = asyncio.Semaphore(55)  # Limit to 55 concurrent requests
        async with semaphore:
            headers = {
                "Authorization": f"Bearer {await self.token_manager.get_access_token()}",
                "Content-Type": "application/json; charset=utf-8"
            }
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/{app_id}/tickets/{ticket_id}/assets"
                try:
                    async with session.get(url, headers=headers) as response:
                        if response.status != 200:
                            raise Exception(f"Failed to get assets for ticket {ticket_id}: {response.status}")
                        assets_data = await response.json()
                        if not isinstance(assets_data, list):
                            raise ValueError("Expected a list of assets")
                        for item in assets_data:
                            if not isinstance(item, dict):
                                raise ValueError("Expected a dictionary in assets list")
                            if "Attributes" in item and not item["Attributes"]:
                                item["Attributes"] = [{}]  # Handle empty Attributes per documentation
                            item["ticket_id"] = ticket_id
                        return assets_data
                except Exception:
                    raise
                finally:
                    await asyncio.sleep(2.0)  # Respect rate limit (60 calls/60s)