import json
import os
import sys

from dotenv import load_dotenv
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload


def get_drive_service():
    """Authenticate with Google Drive using service account credentials."""
    # Support file path (local) or inline JSON (GitHub Actions)
    creds_file = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE")
    creds_json = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")

    if creds_file:
        with open(creds_file) as f:
            creds_info = json.load(f)
    elif creds_json:
        creds_info = json.loads(creds_json)
    else:
        print("Error: Set GOOGLE_SERVICE_ACCOUNT_FILE or GOOGLE_SERVICE_ACCOUNT_JSON")
        sys.exit(1)
    creds = service_account.Credentials.from_service_account_info(
        creds_info, scopes=["https://www.googleapis.com/auth/drive.readonly"]
    )
    return build("drive", "v3", credentials=creds)


def download_latest_csv(folder_id, output_path):
    """Download the most recently modified CSV from a Google Drive folder."""
    service = get_drive_service()

    # Find CSV files in the folder, sorted by most recent
    results = (
        service.files()
        .list(
            q=f"'{folder_id}' in parents and name contains '.csv' and trashed=false",
            orderBy="modifiedTime desc",
            pageSize=1,
            fields="files(id, name, modifiedTime)",
        )
        .execute()
    )

    files = results.get("files", [])
    if not files:
        print("No CSV files found in the Google Drive folder")
        return None

    latest = files[0]
    print(f"Downloading: {latest['name']} (modified: {latest['modifiedTime']})")

    request = service.files().get_media(fileId=latest["id"])
    with open(output_path, "wb") as f:
        downloader = MediaIoBaseDownload(f, request)
        done = False
        while not done:
            _, done = downloader.next_chunk()

    print(f"Saved to: {output_path}")
    return output_path


def main():
    load_dotenv()

    folder_id = os.getenv("GOOGLE_DRIVE_FOLDER_ID")
    if not folder_id:
        print("Error: GOOGLE_DRIVE_FOLDER_ID environment variable not set")
        sys.exit(1)

    output_path = os.getenv("STRONG_CSV_PATH", "strong_export.csv")
    result = download_latest_csv(folder_id, output_path)
    if not result:
        sys.exit(1)


if __name__ == "__main__":
    main()
