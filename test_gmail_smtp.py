import smtplib
from email.mime.text import MIMEText

# Gmail SMTP settings
smtp_server = 'smtp.gmail.com'
smtp_port = 587
gmail_user = 'hensonrichard2000@gmail.com'
gmail_password = 'fnmf fzhl orcr pxmm'  # Your Gmail app password

# Email content
from_email = gmail_user
to_email = 'hensonrichard2000@gmail.com'  # You can change this to any test email
subject = 'SMTP Test Email'
body = 'This is a test email sent from a raw Python script using Gmail SMTP.'

# Compose message
msg = MIMEText(body)
msg['Subject'] = subject
msg['From'] = from_email
msg['To'] = to_email

try:
    # Connect to Gmail's SMTP server using TLS
    server = smtplib.SMTP(smtp_server, smtp_port)
    server.ehlo()
    server.starttls()
    server.login(gmail_user, gmail_password)
    server.send_message(msg)
    server.quit()

    print("✅ Email sent successfully!")
except Exception as e:
    print(f"❌ Failed to send email: {e}")
