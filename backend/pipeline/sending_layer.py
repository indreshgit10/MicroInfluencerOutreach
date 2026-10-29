"""
Sending Layer and Outreach Tracker
Manages the delivery and dispatch of personalized outreach messages:
- Selects candidates with verified contact emails
- Simulates or dispatches via SMTP
- Enforces strict duplicate prevention (idempotency check)
- Handles simulated Instagram DM dispatch workflow
- Maintains a persistent outreach tracker log (JSON and CSV)
"""

import json
import logging
import csv
import smtplib
import sys
from pathlib import Path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.config import (
    OUTREACH_DATA_PATH, TRACKER_DATA_PATH, TRACKER_DATA_CSV,
    SENDING_MODE, SMTP_SERVER, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD,
    SENDER_EMAIL, SENDER_NAME
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("SendingLayer")

class OutreachSendingLayer:
    def __init__(self, mode: str = SENDING_MODE):
        self.mode = mode.lower()
        self.history: Dict[str, Dict[str, Any]] = self._load_existing_tracker()

    def _load_existing_tracker(self) -> Dict[str, Dict[str, Any]]:
        """Loads previous outreach logs to prevent duplicate sending."""
        if TRACKER_DATA_PATH.exists():
            try:
                with open(TRACKER_DATA_PATH, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    # Index by recipient email or identifier
                    return {item.get("recipient_key", item.get("email", "")): item for item in data}
            except Exception as e:
                logger.warning(f"Could not load previous outreach tracker: {e}")
        return {}

    def is_duplicate(self, email: str, name: str) -> bool:
        """Checks if outreach has already been recorded for this recipient."""
        key = email.lower() if (email and email != "Not Found") else name.lower()
        return key in self.history

    def send_smtp_email(self, to_email: str, subject: str, body: str) -> tuple[bool, str]:
        """Sends an authentic email using configured SMTP server."""
        if not SMTP_USERNAME or not SMTP_PASSWORD:
            return False, "SMTP credentials not configured. Switched to simulated delivery."
        try:
            msg = MIMEMultipart()
            msg["From"] = f"{SENDER_NAME} <{SENDER_EMAIL}>"
            msg["To"] = to_email
            msg["Subject"] = subject
            msg.attach(MIMEText(body, "plain", "utf-8"))

            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=10) as server:
                server.starttls()
                server.login(SMTP_USERNAME, SMTP_PASSWORD)
                server.send_message(msg)
            return True, "Email successfully dispatched via SMTP TLS."
        except Exception as e:
            return False, f"SMTP delivery failure: {str(e)}"

    def process_outreach(self, candidates: List[Dict[str, Any]] = None, simulate_all: bool = True) -> List[Dict[str, Any]]:
        """
        Executes the outreach sending workflow:
        1. Selects influencers with valid email.
        2. Retrieves personalized email message.
        3. Sends or simulates sending the email.
        4. Records the sending status.
        5. Prevents duplicate outreach.
        6. Maintains outreach log.
        """
        if candidates is None:
            if not OUTREACH_DATA_PATH.exists():
                raise FileNotFoundError(f"Outreach data not found at {OUTREACH_DATA_PATH}. Run personalization first.")
            with open(OUTREACH_DATA_PATH, "r", encoding="utf-8") as f:
                candidates = json.load(f)

        logger.info(f"Processing outreach for {len(candidates)} candidates in '{self.mode}' mode...")
        tracker_logs = list(self.history.values())
        processed_keys = set(self.history.keys())

        for c in candidates:
            name = c.get("name", "Unknown")
            email = c.get("contact_email", "Not Found").strip()
            subject = c.get("email_subject", "")
            pitch = c.get("email_pitch", "")
            ig_dm = c.get("instagram_dm", "")
            channel = c.get("primary_outreach_channel", "EMAIL")

            recipient_key = email.lower() if (email and email != "Not Found") else name.lower()
            current_time = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

            # 1. Duplicate Prevention Check
            if recipient_key in processed_keys:
                logger.info(f"Duplicate prevented for {name} ({recipient_key}). Skipping.")
                continue

            # 2. Validation & Dispatch Route
            if email and email != "Not Found" and "@" in email:
                if self.mode == "smtp" and not simulate_all:
                    success, detail = self.send_smtp_email(email, subject, pitch)
                    status = "SENT" if success else "FAILED"
                else:
                    status = "SIMULATED"
                    detail = "MIME delivery payload rendered and simulated successfully (anti-spam sandbox mode)."

                log_entry = {
                    "recipient_key": recipient_key,
                    "influencer": name,
                    "email": email,
                    "channel": "EMAIL",
                    "subject": subject,
                    "message_generated": pitch,
                    "sent_date": current_time,
                    "status": status,
                    "delivery_details": detail
                }
            elif ig_dm:
                # Instagram DM Workflow per assignment:
                # "demonstrate the generated DM and create a simulated/manual sending workflow."
                log_entry = {
                    "recipient_key": recipient_key,
                    "influencer": name,
                    "email": "Not Found",
                    "channel": "INSTAGRAM_DM",
                    "subject": "Instagram Direct Message",
                    "message_generated": ig_dm,
                    "sent_date": current_time,
                    "status": "DM_READY_FOR_DISPATCH",
                    "delivery_details": "Instagram DM generated and staged in manual dispatch console."
                }
            else:
                log_entry = {
                    "recipient_key": recipient_key,
                    "influencer": name,
                    "email": "Not Found",
                    "channel": "NONE",
                    "subject": "N/A",
                    "message_generated": "None",
                    "sent_date": current_time,
                    "status": "SKIPPED_NO_CONTACT",
                    "delivery_details": "No verified email or direct social messaging route found."
                }

            tracker_logs.append(log_entry)
            processed_keys.add(recipient_key)
            self.history[recipient_key] = log_entry

        logger.info(f"Outreach processing complete. Total log records: {len(tracker_logs)}")
        self.save_artifacts(tracker_logs)
        return tracker_logs

    def save_artifacts(self, tracker_logs: List[Dict[str, Any]]):
        """Saves outreach tracker records to JSON and CSV."""
        with open(TRACKER_DATA_PATH, "w", encoding="utf-8") as f:
            json.dump(tracker_logs, f, indent=2, ensure_ascii=False)
        logger.info(f"Saved outreach tracker JSON to {TRACKER_DATA_PATH}")

        # CSV format matching assignment specification:
        # Influencer | Email | Message Generated | Sent Date | Status
        fieldnames = ["influencer", "email", "channel", "subject", "message_generated", "sent_date", "status", "delivery_details"]
        with open(TRACKER_DATA_CSV, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            for r in tracker_logs:
                # Clean newline formatting for CSV readability
                row = dict(r)
                row["message_generated"] = row.get("message_generated", "").replace("\n", " ")
                writer.writerow(row)
        logger.info(f"Saved outreach tracker CSV to {TRACKER_DATA_CSV}")

if __name__ == "__main__":
    sender = OutreachSendingLayer(mode="simulation")
    logs = sender.process_outreach(simulate_all=True)
    print(f"Recorded {len(logs)} outreach tracker log entries.")
