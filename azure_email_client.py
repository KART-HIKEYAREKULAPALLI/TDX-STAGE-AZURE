from azure.communication.email import EmailClient
from datetime import datetime

class AzureEmailClient:
    """A class to manage sending email notifications via Azure Communication Services."""
    
    def __init__(self, connection_string: str, sender_address: str,recipient: list):
        """
        Initialize the AzureEmailClient with a connection string.
        
        Args:
            connection_string (str): The Azure Communication Services connection string.
        """
        self.client = EmailClient.from_connection_string(connection_string)
        self.sender_address = sender_address
        self.recipient = recipient

    async def send_error_email(self, error_message: str, subject: str = "Error Notification") -> str:
        """
        Send an email notification with an error message to the specified recipient.
        
        Args:
            recipient (str): The email address of the recipient.
            error_message (str): The error message to include in the email body.
            subject (str, optional): The subject line of the email. Defaults to "Error Notification".

        Returns:
            str: The message ID of the sent email.

        Raises:
            Exception: If the email sending process fails.
        """
        try:
            message = {
                "senderAddress": self.sender_address,
                "recipients": {
                    "to": self.recipient
                },
                "content": {
                    "subject": subject,
                    "plainText": f"Error occurred at {datetime.now().strftime('%Y-%m-%d %H:%M:%S CDT')}:\n{error_message}",
                    "html": f"""
                    <html>
                        <body>
                            <h1>Error Notification</h1>
                            <p>Error occurred at {datetime.now().strftime('%Y-%m-%d %H:%M:%S CDT')}:</p>
                            <p>{error_message}</p>
                        </body>
                    </html>"""
                }
            }

            poller = self.client.begin_send(message)
            result = poller.result()
            print(f"Error email sent to {self.recipient} with message ID: {result.get("id")}")
            return result["id"]

        except Exception as ex:
            print(f"Failed to send error email: {ex}")
            raise
