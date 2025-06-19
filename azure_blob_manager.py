import asyncio
from azure.storage.blob.aio import BlobServiceClient
import json
import uuid

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
                await asyncio.sleep(0.2)