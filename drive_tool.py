import os
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build
from langchain.tools import tool

SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]


def get_drive_service():
    """Build Google Drive service using service account credentials."""

    creds_json = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")

    if not creds_json:
        raise ValueError("GOOGLE_SERVICE_ACCOUNT_JSON environment variable not set.")

    creds_dict = json.loads(creds_json)

    credentials = service_account.Credentials.from_service_account_info(
        creds_dict,
        scopes=SCOPES
    )

    return build("drive", "v3", credentials=credentials)


def get_all_folder_ids(service, root_folder_id):
    """
    Get root folder ID + all subfolder IDs inside it.
    This makes folder search recursive.
    """

    folder_ids = [root_folder_id]
    folders_to_check = [root_folder_id]

    while folders_to_check:
        current_folder_id = folders_to_check.pop()

        query = (
            f"'{current_folder_id}' in parents "
            f"and mimeType = 'application/vnd.google-apps.folder' "
            f"and trashed = false"
        )

        response = service.files().list(
            q=query,
            fields="files(id, name)",
            supportsAllDrives=True,
            includeItemsFromAllDrives=True
        ).execute()

        subfolders = response.get("files", [])

        for folder in subfolders:
            folder_id = folder["id"]
            folder_ids.append(folder_id)
            folders_to_check.append(folder_id)

    return folder_ids


def build_parent_query(folder_ids):
    """
    Build Google Drive query for multiple folders.

    Example:
    'folder1' in parents or 'folder2' in parents
    """

    parent_conditions = []

    for folder_id in folder_ids:
        parent_conditions.append(f"'{folder_id}' in parents")

    return " or ".join(parent_conditions)


@tool
def search_drive_files(query: str) -> str:
    """
    Search files in Google Drive using a query string.

    The query should follow Google Drive API q parameter format.

    Examples:
      - name contains 'report'
      - mimeType = 'application/pdf'
      - fullText contains 'invoice'
      - name contains 'budget' and mimeType = 'application/vnd.google-apps.spreadsheet'
      - modifiedTime > '2024-01-01T00:00:00'

    Returns a list of matching files with name, type, link, and modified date.
    """

    try:
        service = get_drive_service()

        folder_id = os.environ.get("DRIVE_FOLDER_ID", "").strip()

        if folder_id:
            all_folder_ids = get_all_folder_ids(service, folder_id)
            parent_query = build_parent_query(all_folder_ids)

            full_query = f"({parent_query}) and ({query}) and trashed = false"
        else:
            full_query = f"({query}) and trashed = false"

        results = service.files().list(
            q=full_query,
            pageSize=10,
            fields="files(id, name, mimeType, modifiedTime, webViewLink)",
            supportsAllDrives=True,
            includeItemsFromAllDrives=True
        ).execute()

        files = results.get("files", [])

        if not files:
            return "No files found matching your search."

        output = f"Found {len(files)} file(s):\n\n"

        for i, file in enumerate(files, 1):
            mime = file.get("mimeType", "unknown")

            mime_readable = {
                "application/pdf": "PDF",
                "application/vnd.google-apps.document": "Google Doc",
                "application/vnd.google-apps.spreadsheet": "Google Sheet",
                "application/vnd.google-apps.presentation": "Google Slides",
                "application/vnd.google-apps.folder": "Folder",
                "image/jpeg": "Image (JPEG)",
                "image/png": "Image (PNG)",
                "text/plain": "Text File",
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "Word Document",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": "Excel File",
                "application/vnd.openxmlformats-officedocument.presentationml.presentation": "PowerPoint File",
            }.get(mime, mime.split("/")[-1])

            output += f"{i}. **{file.get('name', 'Unnamed file')}**\n"
            output += f"   Type: {mime_readable}\n"
            output += f"   Modified: {file.get('modifiedTime', 'N/A')[:10]}\n"
            output += f"   Link: {file.get('webViewLink', 'N/A')}\n\n"

        return output

    except json.JSONDecodeError:
        return "Error: GOOGLE_SERVICE_ACCOUNT_JSON is not valid JSON. Please check your .env file."

    except Exception as e:
        return f"Error searching Drive: {str(e)}"