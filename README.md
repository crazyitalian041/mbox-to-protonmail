MBOX to Proton Mail Import Tool

This script imports large MBOX email archives into Proton Mail using Proton Mail Bridge v4.

It supports:
	•	Migrating from HEY, Gmail, Outlook, or any service exporting .mbox
	•	Very large archives (100k+ messages)
	•	Repairing malformed email headers
	•	Avoiding duplicates using Proton Mail deduplication
	•	Resuming interrupted imports

⸻

Dependencies

This script uses both built-in Python modules and two external libraries.

External Libraries (Install with pip)

These libraries must be installed manually:

(IMPORTANT: Replace ``` with actual backticks AFTER pasting)

```bash
pip install imapclient chardet
```

Built-in Python Modules (No installation needed)

These modules come with Python automatically:
	•	email
	•	os
	•	time
	•	mailbox
	•	datetime

Full Import List

```python
from imapclient import IMAPClient
import chardet

import email
import os
import time
import mailbox
import datetime
```

⸻

Proton Mail Bridge Setup
	1.	Install Proton Mail Bridge v4
	2.	Add your Proton Mail account
	3.	Open Mailbox Details
	4.	Copy the IMAP Username and IMAP Password

Do not use your email address as the IMAP username.
Use the Bridge-generated username.

⸻

Finding the Correct IMAP Folder Name

In Thunderbird:
	1.	Right-click the folder
	2.	Select “Properties”
	3.	Read the “Location” field

Example:

imap://pm_abcdef@127.0.0.1/Folders/Hey Archive

This means the correct IMAP folder name is:

Folders/Hey Archive

⸻

Running the Import

Run the script:

```bash
python3 upload_mbox.py
```

⸻

Resume Support

If some emails were already imported:

ALREADY_UPLOADED = 6648  

The script will skip that many messages from the MBOX file.

⸻

Troubleshooting

“no such user”
	•	You used your email address instead of the IMAP username.

“no such mailbox”
	•	Folder name is wrong. Check Thunderbird properties.

“expected CR”
	•	Client sent invalid CRLF. Script corrects this.

⸻

License

MIT License

⸻

AFTER YOU PASTE

Replace every \``` with real backticks (```), since escaped backticks are now safe.

⸻
