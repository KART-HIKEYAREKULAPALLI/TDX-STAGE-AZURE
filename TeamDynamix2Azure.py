import aiohttp
import asyncio
from azure.storage.blob.aio import BlobServiceClient
from datetime import datetime, timedelta
import json
import uuid
import asyncio
import os
from datetime import datetime, timedelta
from dotenv import dotenv_values, set_key

# Load environment variables
config = dotenv_values(".env")

class TokenManager:
    """Manages authentication tokens for the TeamDynamix API."""
    
    def __init__(self, username: str, password: str):
        """
        Initialize the TokenManager with credentials and authentication URL.
        
        Args:
            username (str): API username.
            password (str): API password.
            auth_url (str): Authentication endpoint URL.
        """
        self.username = username
        self.password = password
        self.auth_url = "https://servicecenter.midlandhealth.org/TDWebApi/api/auth"
        self.access_token = None
        self.expires_at = None
        self.payload = {"UserName": self.username, "Password": self.password}

    async def authenticate(self) -> None:
        """Authenticates with the TeamDynamix API and updates token information."""
        async with aiohttp.ClientSession() as session:
            async with session.post(self.auth_url, json=self.payload) as response:
                response.raise_for_status()
                self.access_token = await response.text()
                self.expires_at = datetime.now() + timedelta(hours=24)

    async def refresh_token(self) -> None:
        """Refreshes the access token."""
        await self.authenticate()

    async def get_access_token(self) -> str:
        """
        Returns the current access token, refreshing if necessary.
        
        Returns:
            str: Valid access token.
        """
        if not self.access_token or self.expires_at < datetime.now():
            await self.refresh_token()
        
        return str(self.access_token)

class AzureBlobDataManager:
    """Manages data uploads to Azure Blob Storage."""
    
    def __init__(self, connection_string: str, container: str = "teamdynamics"):
        """
        Initialize the AzureBlobDataManager.
        
        Args:
            connection_string (str): Azure Blob Storage connection string.
            container (str): Name of the container.
        """
        self.connection_string = connection_string
        self.container = container

    async def upload_data(self, folder_name: str, data: dict) -> None:
        """
        Uploads data to Azure Blob Storage within a specified folder.
        
        Args:
            folder_name (str): Folder name within the container.
            data (dict): Data to be uploaded as JSON.
        """
        async with BlobServiceClient.from_connection_string(self.connection_string) as blob_service_client:
            async with blob_service_client.get_container_client(self.container) as container_client:
                random_blob_name = str(uuid.uuid4())
                blob_client = container_client.get_blob_client(f"{folder_name}/{random_blob_name}.json")
                await blob_client.upload_blob(json.dumps(data).encode("utf-8"), overwrite=True)
                await asyncio.sleep(1)



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
        ResponsibilityUids: str = None,
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
                if ResponsibilityUids is not None:
                    params["ResponsibilityUids"] = str(ResponsibilityUids)

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


async def extract_daily_tickets(tdx_client: TeamDynamixClient, azure_blob_manager: AzureBlobDataManager, date: datetime) -> None:
    """
    Extracts tickets for a specific date, along with their details, feed, and assets, and uploads to Azure Blob Storage.

    Args:
        tdx_client (TeamDynamixClient): TeamDynamix API client instance.
        azure_blob_manager (AzureBlobDataManager): Azure Blob Storage manager instance.
        date (datetime): Date to extract tickets for (00:00 to 23:59).
    """
    # Search tickets for the given date
    tickets = await tdx_client.search_tickets(date=date)
    
    # Process each ticket
    for ticket in tickets:
        ticket_id = ticket["ID"]
        
        # Get and upload ticket details
        try:
            details = await tdx_client.get_ticket_details(ticket_id)
            await azure_blob_manager.upload_data(
                f"TICKET_DETAIL/{date.strftime('%Y-%m')}",
                {"ticket_id": ticket_id, "details": details}
            )
        except Exception:
            pass  # Skip errors to continue processing
        
        # Get and upload ticket feed
        try:
            feed = await tdx_client.get_ticket_feed(ticket_id)
            await azure_blob_manager.upload_data(
                f"TICKET_FEED/{date.strftime('%Y-%m')}",
                {"ticket_id": ticket_id, "feed": feed}
            )
        except Exception:
            pass  # Skip errors to continue processing
        
        # Get and upload ticket assets
        try:
            assets = await tdx_client.get_ticket_assets(ticket_id)
            await azure_blob_manager.upload_data(
                f"TICKET_ASSETS/{date.strftime('%Y-%m')}",
                {"ticket_id": ticket_id, "assets": assets}
            )
        except Exception:
            pass  # Skip errors to continue processing

async def main():
    """
    Main function to extract historical ticket data from LAST_RUN_TIME (or January 1, 2025) to current date,
    and upload details, feed, and assets to Azure Blob Storage. Updates LAST_RUN_TIME after each run.
    """
    # Retrieve credentials from .env
    username = config.get("TDX_USERNAME")
    password = config.get("TDX_PASSWORD")
    azure_connection_string = config.get("AZURE_CONNECTION_STRING")
    last_run_time_str = os.getenv("LAST_RUN_TIME")

    print(username,password,azure_connection_string,last_run_time_str)

    # Validate credentials
    if not all([username, password, azure_connection_string]):
        raise ValueError("Missing required environment variables in .env file")

    
    if last_run_time_str:
        try:
            start_date = datetime.fromisoformat(last_run_time_str)
        except ValueError:
            print("Invalid LAST_RUN_TIME format in .env; defaulting to January 1, 2025")

    # # Initialize clients
    # token_manager = TokenManager(username, password)
    # await token_manager.authenticate()
    # azure_blob_manager = AzureBlobDataManager(azure_connection_string)
    # tdx_client = TeamDynamixClient(token_manager)

    # # Define date range (from start_date to current date)
    # end_date = datetime.now()  # Current date: June 18, 2025
    # current_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)

    # # Process each day
    # while current_date <= end_date:
    #     await extract_daily_tickets(tdx_client, azure_blob_manager, current_date)
    #     current_date += timedelta(days=1)

    # # # Update LAST_RUN_TIME in .env
    # current_time_str = datetime.now().isoformat()
    # set_key('.env', "LAST_RUN_TIME", current_time_str)

if __name__ == "__main__":
    asyncio.run(main())