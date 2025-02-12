from imapclient import IMAPClient

SERVER = "127.0.0.1"
PORT = 1143  # Use 993 if using SSL
USE_SSL = False
USERNAME = "hi@therob.io"
PASSWORD = "mmA_QXUhELQUkMMr5sWDMg"
DESTINATION_FOLDER = "Folders/Hey Archive"

with IMAPClient(SERVER, port=PORT, ssl=USE_SSL) as client:
    client.login(USERNAME, PASSWORD)
    client.select_folder(DESTINATION_FOLDER)
    messages = client.search(["ALL"])
    print(f"📨 Emails already uploaded: {len(messages)}")
