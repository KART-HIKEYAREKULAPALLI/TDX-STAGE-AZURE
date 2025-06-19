import asyncio
import os
import logging
from datetime import datetime, timedelta
from dotenv import dotenv_values, set_key
from token_manager import TokenManager
from azure_blob_manager import AzureBlobDataManager
from teamdynamix_client import TeamDynamixClient
from azure_email_client import AzureEmailClient

# Load environment variables
config = dotenv_values(".env")


log_file = os.path.join('logs/', f"{datetime.now().strftime('%Y-%m-%d')}.log")
logging.basicConfig(
    filename=log_file,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

async def cleanup_old_logs():
    """Delete log files older than 10 days."""
    now = datetime.now()
    for log_file in os.listdir('logs'):
        log_path = os.path.join('logs', log_file)
        if os.path.isfile(log_path):
            file_date_str = log_file.replace(".log", "")
            try:
                file_date = datetime.strptime(file_date_str, "%Y-%m-%d")
                if (now - file_date).days > 8:
                    os.remove(log_path)
                    logger.info(f"Deleted old log file: {log_path}")
            except ValueError:
                logger.warning(f"Skipping invalid log file name: {log_file}")

async def extract_daily_tickets(tdx_client: TeamDynamixClient, azure_blob_manager: AzureBlobDataManager, 
date: datetime, email_client: AzureEmailClient) -> None:
    logger.info(f"Starting ticket extraction for date: {date.strftime('%Y-%m-%d')}")
    try:
        # Search tickets for the given date
        tickets = await tdx_client.search_tickets(date=date)
        logger.info(f"Found {len(tickets)} tickets for {date.strftime('%Y-%m-%d')}")
        
        # Process each ticket
        for ticket in tickets:
            ticket_id = ticket["ID"]
            app_id = ticket.get("AppID", 156)  # Default to 156 if AppID is missing
            
            # Get and upload ticket details
            try:
                details = await tdx_client.get_ticket_details(ticket_id)
                await azure_blob_manager.upload_data(
                    f"TICKET_DETAIL/{date.strftime('%Y-%m')}",
                    {"ticket_id": ticket_id, "details": details}
                )
                logger.info(f"Uploaded details for ticket ID {ticket_id}")
            except Exception as e:
                error_msg = f"Failed to upload ticket details for ID {ticket_id}: {str(e)}"
                logger.error(error_msg)
                await email_client.send_error_email( error_message= error_msg,
                    subject=f"Error: Ticket Details Upload Failed - {date.strftime('%Y-%m-%d')}")
                raise
            
            # Get and upload ticket feed
            try:
                feed = await tdx_client.get_ticket_feed(ticket_id)
                await azure_blob_manager.upload_data(
                    f"TICKET_FEED/{date.strftime('%Y-%m')}",
                    {"ticket_id": ticket_id, "feed": feed}
                )
                logger.info(f"Uploaded feed for ticket ID {ticket_id}")
            except Exception as e:
                error_msg = f"Failed to upload ticket feed for ID {ticket_id}: {str(e)}"
                logger.error(error_msg)
                await email_client.send_error_email( error_message= error_msg,
                    subject=f"Error: Ticket Feed Upload Failed - {date.strftime('%Y-%m-%d')}")
                raise
            
            # Get and upload ticket assets
            try:
                assets = await tdx_client.get_ticket_assets(ticket_id, app_id=app_id)
                await azure_blob_manager.upload_data(
                    f"TICKET_ASSETS/{date.strftime('%Y-%m')}",
                    {"ticket_id": ticket_id, "assets": assets}
                )
                logger.info(f"Uploaded assets for ticket ID {ticket_id}")
            except Exception as e:
                error_msg = f"Failed to upload ticket assets for ID {ticket_id}: {str(e)}"
                logger.error(error_msg)
                await email_client.send_error_email( error_message= error_msg,
                    subject=f"Error: Ticket Assets Upload Failed - {date.strftime('%Y-%m-%d')}")
                raise

    except Exception as e:
        error_msg = f"Error during ticket extraction for date {date.strftime('%Y-%m-%d')}: {str(e)}"
        logger.error(error_msg)
        await email_client.send_error_email(error_message=error_msg,
            subject=f"Error: Ticket Extraction Failed - {date.strftime('%Y-%m-%d')}")
        raise

async def process_thursday_data(tdx_client: TeamDynamixClient, azure_blob_manager: AzureBlobDataManager, 
date: datetime, email_client: AzureEmailClient) -> None:
    """
    Process Thursday-specific data for the given date, fetching and uploading applications,
    services, and knowledge base articles for app_id=357 to Azure Blob Storage.

    Args:
        tdx_client (TeamDynamixClient): Client for interacting with TeamDynamix API.
        azure_blob_manager (AzureBlobDataManager): Manager for uploading data to Azure Blob Storage.
        date (datetime): The date being processed.
        email_client (AzureEmailClient): Client for sending error emails.

    Raises:
        Exception: If any API call or upload fails, after logging and sending an error email.
    """
    logger.info(f"Processing Thursday-specific data for {date.strftime('%Y-%m-%d')} with app_id=357")

    # Get and upload applications
    try:
        applications = await tdx_client.get_applications()
        await azure_blob_manager.upload_data(
            f"APPLICATIONS/{date.strftime('%Y-%m')}",
            {"date": date.strftime('%Y-%m-%d'), "applications": applications}
        )
        logger.info(f"Uploaded {len(applications)} applications for {date.strftime('%Y-%m-%d')}")
    except Exception as e:
        error_msg = f"Failed to upload applications for {date.strftime('%Y-%m-%d')}: {str(e)}"
        logger.error(error_msg)
        await email_client.send_error_email(
            error_message=error_msg,
            subject=f"Error: Applications Upload Failed - {date.strftime('%Y-%m-%d')}"
        )
        raise

    # Get and upload services
    try:
        services = await tdx_client.get_services(app_id=357)
        await azure_blob_manager.upload_data(
            f"SERVICES/{date.strftime('%Y-%m')}",
            {"date": date.strftime('%Y-%m-%d'), "services": services}
        )
        logger.info(f"Uploaded {len(services)} services for {date.strftime('%Y-%m-%d')}")
    except Exception as e:
        error_msg = f"Failed to upload services for {date.strftime('%Y-%m-%d')}: {str(e)}"
        logger.error(error_msg)
        await email_client.send_error_email(
            error_message=error_msg,
            subject=f"Error: Services Upload Failed - {date.strftime('%Y-%m-%d')}"
        )
        raise

    # Get and upload knowledge base articles
    try:
        # Search for knowledge base article IDs
        knowledge_ids = await tdx_client.search_knowledgebase(app_id=357)
        logger.info(f"Found {len(knowledge_ids)} knowledge base articles for app_id=357")
        for knowledge_id in knowledge_ids:
            try:
                knowledge_data = await tdx_client.get_knowledgebase(app_id=357, knowledge_id=knowledge_id)
                await azure_blob_manager.upload_data(
                    f"KNOWLEDGEBASE/{date.strftime('%Y-%m')}",
                    {"knowledge_id": knowledge_id, "data": knowledge_data}
                )
                logger.info(f"Uploaded knowledge base article ID {knowledge_id} for {date.strftime('%Y-%m-%d')}")
            except Exception as e:
                # Skip invalid knowledge IDs but log the error
                logger.warning(f"Failed to fetch knowledge base article ID {knowledge_id}: {str(e)}")
                continue
    except Exception as e:
        error_msg = f"Failed to process knowledge base articles for {date.strftime('%Y-%m-%d')}: {str(e)}"
        logger.error(error_msg)
        await email_client.send_error_email(
            error_message=error_msg,
            subject=f"Error: Knowledge Base Upload Failed - {date.strftime('%Y-%m-%d')}"
        )
        raise


async def main():
    """
    Main function to extract historical ticket data from LAST_RUN_TIME (or January 1, 2025) to current date,
    and upload details, feed, and assets to Azure Blob Storage. Updates LAST_RUN_TIME after each run.
    """
    logger.info("Starting main execution")
    try:
        # Retrieve credentials from .env
        username = str(config.get("TDX_USERNAME"))
        password = str(config.get("TDX_PASSWORD"))
        azure_connection_string = str(config.get("AZURE_CONNECTION_STRING"))
        last_run_time_str = config.get("LAST_RUN_TIME")
        azure_comm_connection_string = str(config.get("AZURE_COMMUNICATION_CONNECTION_STRING"))
        sender_address = str(config.get("SENDER_ADDRESS"))
        values_string = str(config.get("RECIPIENT"))
        recipient_list = values_string.split(',') 
        recipient = [{"address": value} for value in recipient_list]

        # Validate credentials
        if not all([username, password, azure_connection_string, azure_comm_connection_string, sender_address, values_string]):
            logger.warning("Missing required environment variables in .env file")
            raise ValueError("Missing required environment variables in .env file")

        if last_run_time_str:
            try:
                start_date = datetime.fromisoformat(last_run_time_str)
            except ValueError:
                logger.warning("Invalid LAST_RUN_TIME format in .env; defaulting to January 1, 2025")
                start_date = datetime.now()-timedelta(days=3)
        else:
            start_date = datetime.now()-timedelta(days=3)
        
        current_date = start_date.replace(minute=0, second=0, microsecond=0)


        # # Initialize clients
        token_manager = TokenManager(username=username,password=password)
        await token_manager.authenticate()
        azure_blob_manager = AzureBlobDataManager(connection_string=azure_connection_string)
        tdx_client = TeamDynamixClient(token_manager=token_manager)
        email_client = AzureEmailClient(connection_string= azure_comm_connection_string,sender_address=sender_address,recipient=recipient )


        # Define date range (from start_date to current date)
        end_date = datetime.now()  

        # Cleanup old logs
        await cleanup_old_logs()

        # # Process each day
        while current_date <= end_date:
            # print(current_date)
            # await extract_daily_tickets(tdx_client, azure_blob_manager, current_date, email_client)
            # # Check if the current day is Thursday (weekday() == 3)
            if current_date.weekday() == 3:
                await process_thursday_data(tdx_client, azure_blob_manager, current_date, email_client)
            current_date += timedelta(days=1)

        # Update LAST_RUN_TIME in .env
        current_time_str = datetime.now().isoformat()
        set_key('.env', "LAST_RUN_TIME", current_time_str)
        logger.info(f"Updated LAST_RUN_TIME to {current_time_str}")
    
    except Exception as e:
        logger.error(f"Main execution failed: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
