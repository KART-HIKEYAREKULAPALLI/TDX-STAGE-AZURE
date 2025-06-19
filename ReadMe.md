# TeamDynamix Ticket Extractor
A Python script to extract and process tickets from TeamDynamix, upload data to Azure Blob Storage, and log activities with email notifications for errors.
Overview
This project automates the extraction of historical ticket data (details, feeds, and assets) from the TeamDynamix API, stores it in Azure Blob Storage, and maintains logs with cleanup of old files. It includes error notification via Azure Communication Services email.
Features

# Extracts tickets modified since a configurable start date.
Uploads ticket data to Azure Blob Storage in TICKET_DETAIL, TICKET_FEED, and TICKET_ASSETS folders.
Logs activities to daily files in a logs subfolder, deleting logs older than 10 days.
Sends email notifications for errors to a configured recipient.
Modular design with separate classes for token management, Azure storage, TeamDynamix API, and email services.

##Prerequisites

Python 3.8+
Azure Blob Storage account
Azure Communication Services account
TeamDynamix API credentials

##Installation

Clone the repository
cd AZURE_TEAMDYNAMIX_LINKING 


Create a virtual environment:python -m venv venv
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows


Install dependencies:`pip install -r requirements.txt`


Configure the .env file with your credentials (see .env.example).

Configuration

Copy .env.example to .env and update with your values:

`TDX_USERNAME=your_teamdynamix_username
TDX_PASSWORD=your_teamdynamix_password
AZURE_CONNECTION_STRING=your_azure_connection_string
AZURE_COMMUNICATION_CONNECTION_STRING=your_communication_connection_string
SENDER_ADDRESS=your_sender_address
RECIPIENT=your_recipient_email
LAST_RUN_TIME=  # Optional, updated automatically
`

Keep .env out of version control (already in .gitignore).

Usage
Run the script:
python main.py


Extracts tickets from LAST_RUN_TIME (or 3 days from now) to the current date.
Uploads data to Azure and logs to logs/YYYY-MM-DD.log.
Sends error emails if issues occur.

File Structure
```markdown
TEAMDYNAMIX/
├── venv/              # Virtual environment
├── .env               # Configuration (not tracked)
├── .gitignore         # Excludes venv/, .env, etc.
├── requirements.txt   # Dependencies
├── token_manager.py   # Token management class
├── azure_blob_manager.py  # Azure Blob Storage class
├── teamdynamix_client.py  # TeamDynamix API class
├── azure_email_client.py  # Azure email class
├── main.py            # Main execution script
├── README.md          # This file
└── logs/              # Log files (auto-generated)
```

Contributing
Feel free to fork and submit pull requests. Report issues via the repository's issue tracker.
License
MIT License (add a LICENSE file if desired, e.g., copy from https://choosealicense.com/licenses/mit/).
Contact
For questions, contact your_email@example.com.

### Additional Steps

1. **Create `.env.example`**:
   - Add a template file to guide users:
     ```bash
     echo "TDX_USERNAME=\nTDX_PASSWORD=\nAZURE_CONNECTION_STRING=\nAZURE_COMMUNICATION_CONNECTION_STRING=\nSENDER_ADDRESS=\nRECIPIENT=\nLAST_RUN_TIME=" > .env.example
     ```
   - Commit this file to Git:
     ```bash
     git add .env.example
     git commit -m "Add .env.example for configuration guide"
     git push origin main
     ```


     ```
2. **Push Changes**:
   - After adding the README and `.env.example`:
     ```bash
     git add README.md .env.example
     git commit -m "Add README and .env.example"
     git push origin main
     ```

### Notes

- **Contact Email**: karthikeya.rekulapalli@midlandhealth.org
- **Simplicity**: The README is kept simple with essential sections (Overview, Installation, Usage, etc.) suitable for a small project.
- **Current Date**: Reflects June 19, 2025, 11:06 AM CDT, ensuring the README is up-to-date.
- **Testing**: Verify the README instructions by cloning the repository in a new directory and following the steps.

This process sets up your Git repository and provides a clear README for users. Let me know if you need help with specific Git commands or README customization!

