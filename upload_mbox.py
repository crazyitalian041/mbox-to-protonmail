from imapclient import IMAPClient
import email
import os
import time
import mailbox
import chardet
import datetime

# Proton Mail Bridge IMAP credentials
SERVER = "127.0.0.1"
PORT = 1143  # Use 993 if using SSL
USE_SSL = False
USERNAME = "hi@therob.io"
PASSWORD = "mmA_QXUhELQUkMMr5sWDMg"

MBOX_FILE = "/Users/robertdejesus/Downloads/HEY-emails-rawb@hey.com.mbox"
DESTINATION_FOLDER = "Folders/Hey Archive"

BATCH_SIZE = 5  # Number of emails to process at a time
ALREADY_UPLOADED = 98235  # Update this number after checking uploaded count
MAX_EMAIL_SIZE = 30 * 1024 * 1024  # 30MB limit
RETRY_DELAY = 10  # Wait 10 seconds on 502 errors

# Log skipped emails
SKIPPED_EMAILS_LOG = "/Users/robertdejesus/skipped_emails.log"

# Function to detect file encoding
def detect_encoding(file_path):
    with open(file_path, "rb") as f:
        raw_data = f.read(100000)  # Read a sample to detect encoding
        result = chardet.detect(raw_data)
        return result["encoding"]

# Function to ensure an email has a valid Date header
def fix_missing_date(msg):
    if "Date" not in msg or not msg["Date"].strip():
        new_date = datetime.datetime.now().strftime("%a, %d %b %Y %H:%M:%S +0000")
        if "Date" in msg:
            msg.replace_header("Date", new_date)
        else:
            msg.add_header("Date", new_date)
        print(f"🔧 Fixed missing Date header: {new_date}")
    return msg

# Function to log skipped emails
def log_skipped_email(email_index, reason):
    with open(SKIPPED_EMAILS_LOG, "a") as log_file:
        log_file.write(f"Email {email_index} skipped: {reason}\n")

def upload_mbox(mbox_file, folder):
    if not os.path.exists(mbox_file):
        print(f"❌ Error: MBOX file not found at {mbox_file}")
        return

    encoding = detect_encoding(mbox_file)
    print(f"📄 Detected encoding: {encoding}")

    print(f"📡 Connecting to IMAP server at {SERVER}:{PORT}...")

    try:
        with IMAPClient(SERVER, port=PORT, ssl=USE_SSL) as client:
            client.login(USERNAME, PASSWORD)

            # Check if the folder exists
            print(f"📂 Selecting folder: {folder}...")
            try:
                client.select_folder(folder)
            except Exception as e:
                print(f"❌ Error: Cannot select folder '{folder}' – {e}")
                return

            # Process MBOX file using mailbox module (efficient)
            print(f"📤 Uploading emails from {mbox_file} to '{folder}'...")
            mbox = mailbox.mbox(mbox_file)
            total = len(mbox)
            print(f"📨 Found {total} emails in MBOX.")

            emails_to_upload = total - ALREADY_UPLOADED
            print(f"⏩ Skipping {ALREADY_UPLOADED} already uploaded emails.")
            print(f"📤 Need to upload {emails_to_upload} emails.")

            for index, msg in enumerate(mbox, start=1):
                if index <= ALREADY_UPLOADED:
                    continue  # Skip already uploaded emails

                # Ensure the email has a Date header
                msg = fix_missing_date(msg)

                # Convert message to string and check size
                email_data = msg.as_string().encode("utf-8")
                if len(email_data) > MAX_EMAIL_SIZE:
                    print(f"\n❌ Skipping email {index}: Exceeds 30MB size limit")
                    log_skipped_email(index, "Exceeds 30MB size limit")
                    continue

                # Retry logic for 502 errors
                retries = 3
                while retries > 0:
                    try:
                        client.append(folder, email_data)
                        print(f"✅ Uploaded {index}/{total} emails...", end="\r")
                        break  # Exit retry loop on success
                    except Exception as upload_error:
                        error_message = str(upload_error)

                        # Check for 502 error
                        if "502" in error_message:
                            print(f"\n🔄 Retrying email {index} after {RETRY_DELAY} seconds due to 502 error...")
                            time.sleep(RETRY_DELAY)
                            retries -= 1
                            continue  # Retry sending the email
                        
                        # Log any other failures
                        print(f"\n❌ Failed to upload email {index}: {upload_error}")
                        log_skipped_email(index, f"Failed to upload: {upload_error}")
                        break  # Stop retrying on non-502 errors

                # Process emails in small batches
                if index % BATCH_SIZE == 0:
                    time.sleep(0.1)  # Small delay to avoid rate limits

            print("\n✅ Upload complete!")

    except Exception as e:
        print(f"❌ Error: {e}")

# Run the upload process
upload_mbox(MBOX_FILE, DESTINATION_FOLDER)
