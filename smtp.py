import asyncio
import logging
from email import message_from_bytes
from aiosmtpd.controller import Controller

# Configure logging for clear output
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

class SpoofHandler:
    async def handle_DATA(self, server, session, envelope):
        logging.info('--- Received Email ---')
        logging.info(f"Sender: {envelope.mail_from}")
        logging.info(f"Recipients: {envelope.rcpt_tos}")
        try:
            # Parse the raw email bytes into a MIME message
            msg = message_from_bytes(envelope.content)
            logging.info(f"Subject: {msg.get('Subject')}")
            logging.info("Email Content:")
            if msg.is_multipart():
                # Walk through all parts of the MIME message
                for part in msg.walk():
                    # Skip container parts
                    if part.is_multipart():
                        continue
                    content_type = part.get_content_type()
                    payload = part.get_payload(decode=True)
                    charset = part.get_content_charset() or 'utf-8'
                    # Handle text parts separately
                    if content_type == 'text/plain':
                        text = payload.decode(charset, errors='replace')
                        logging.info(f"Text part:\n{text}")
                    elif content_type == 'text/html':
                        html = payload.decode(charset, errors='replace')
                        logging.info(f"HTML part:\n{html}")
                    else:
                        # Log details for attachments or other parts
                        filename = part.get_filename()
                        if filename:
                            logging.info(f"Attachment: {filename} ({content_type}, {len(payload)} bytes)")
                        else:
                            logging.info(f"Part: {content_type} ({len(payload)} bytes)")
            else:
                # For non-multipart emails, simply decode and log
                content = envelope.content.decode('utf8', errors='replace')
                logging.info(content)
        except Exception as e:
            logging.error(f"Error parsing email: {e}")
            logging.info("Raw content:")
            logging.info(envelope.content.decode('utf8', errors='replace'))
        logging.info('----------------------')
        return '250 Message accepted'

if __name__ == '__main__':
    # Start the SMTP server on port 1025
    controller = Controller(SpoofHandler(), hostname='0.0.0.0', port=1025)
    controller.start()
    logging.info("SMTP server running on port 1025. Press Ctrl+C to stop.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        controller.stop()
