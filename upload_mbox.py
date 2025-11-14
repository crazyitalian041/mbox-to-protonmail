from imapclient import IMAPClient
import email
import os
import time
import mailbox
import chardet
import datetime

# Proton Mail Bridge IMAP credentials
SERVER = "127.0.0.1"
PORT = 1143
USE_SSL = False           # Proton Bridge uses STARTTLS internally but appears as plain IMAP
USERNAME = "usernamefrombridge"
PASSWORD = "PASSWORD"

# Paths
MBOX_FILE = "MBOXFILENAME.mbox"
DESTINATION_FOLDER = "Destinationpath"

# Settings
BATCH_SIZE = 5
ALREADY_UPLOADED = 0
MAX_EMAIL_SIZE = 30 * 1024 * 1024  # 30 MB
RETRY_DELAY = 10
SKIPPED_EMAILS_LOG = "skipped_emails.log"


# ---------------------------
# UTILITIES
# ---------------------------

def detect_encoding(file_path):
    """Detect file encoding."""
    with open(file_path, "rb") as f:
        raw_data = f.read(100000)
        result = chardet.detect(raw_data)
        return result["encoding"]


def fix_missing_date(msg):
    """Ensure email has a Date header."""
    if "Date" not in msg or not msg["Date"].strip():
        new_date = datetime.datetime.now().strftime("%a, %d %b %Y %H:%M:%S +0000")
        if "Date" in msg:
            msg.replace_header("Date", new_date)
        else:
            msg.add_header("Date", new_date)
        print(f"🔧 Fixed missing Date header: {new_date}")
    return msg


def log_skipped_email(email_index, reason):
    """Log skipped emails."""
    with open(SKIPPED_EMAILS_LOG, "a") as log_file:
        log_file.write(f"Email {email_index} skipped: {reason}\n")


# ---------------------------
# MAIN UPLOAD FUNCTION
# ---------------------------

def upload_mbox(mbox_file, folder):

    if not os.path.exists(mbox_file):
        print(f"❌ Error: MBOX file not found at {mbox_file}")
        return

    encoding = detect_encoding(mbox_file)
    print(f"📄 Detected encoding: {encoding}")

    print(f"📡 Connecting to IMAP server at {SERVER}:{PORT}...")

    try:
        with IMAPClient(SERVER, port=PORT, ssl=USE_SSL) as client:

            # ----------------------------------------------------------
            # PROTON MAIL BRIDGE v4 FIX: FORCE CRLF + USE LOGIN METHOD
            # ----------------------------------------------------------
            # Fixes "expected CR" and "unknown command authenticate"
            client._imap._crlf = '\r\n'

            # Perform login with proper CRLF termination
            client.login(USERNAME, PASSWORD)
            print("🔐 Authenticated successfully.")

            # ----------------------------------------------------------
            # SELECT THE DESTINATION FOLDER
            # ----------------------------------------------------------
            print(f"📂 Selecting folder: {folder}...")
            try:
                client.select_folder(folder)
            except Exception as e:
                print(f"❌ Error: Cannot select folder '{folder}' – {e}")
                return

            # ----------------------------------------------------------
            # PROCESS MBOX
            # ----------------------------------------------------------
            print(f"📤 Uploading emails from {mbox_file} to '{folder}'...")
            mbox = mailbox.mbox(mbox_file)
            total = len(mbox)
            print(f"📨 Found {total} emails in MBOX.")

            emails_to_upload = total - ALREADY_UPLOADED
            print(f"⏩ Skipping {ALREADY_UPLOADED} already uploaded emails.")
            print(f"📤 Need to upload {emails_to_upload} emails.")

            for index, msg in enumerate(mbox, start=1):

                if index <= ALREADY_UPLOADED:
                    continue

                # Ensure valid Date header
                msg = fix_missing_date(msg)

                # Convert to bytes
                email_data = msg.as_bytes()

                # Size limit
                if len(email_data) > MAX_EMAIL_SIZE:
                    print(f"\n❌ Skipping email {index}: exceeds 30MB limit")
                    log_skipped_email(index, "Exceeds 30MB limit")
                    continue

                # Upload with retries
                retries = 3
                while retries > 0:
                    try:
                        client.append(folder, email_data)
                        print(f"✅ Uploaded {index}/{total} emails...", end="\r")
                        break
                    except Exception as upload_error:
                        error_message = str(upload_error)

                        if "502" in error_message:
                            print(f"\n🔄 Retrying email {index} after {RETRY_DELAY}s...")
                            time.sleep(RETRY_DELAY)
                            retries -= 1
                            continue

                        print(f"\n❌ Failed to upload email {index}: {upload_error}")
                        log_skipped_email(index, f"Upload failed: {upload_error}")
                        break

                # small delay to avoid rate limits
                if index % BATCH_SIZE == 0:
                    time.sleep(0.1)

            print("\n🎉 Upload complete!")

    except Exception as e:
        print(f"❌ Fatal Error: {e}")


# ---------------------------
# RUN
# ---------------------------
upload_mbox(MBOX_FILE, DESTINATION_FOLDER)
