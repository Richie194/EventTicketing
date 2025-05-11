import smtplib
from email.mime.text import MIMEText

# Gmail SMTP settings (SSL)
smtp_server = 'smtp.gmail.com'
smtp_port = 465
gmail_user = 'hensonrichard2000@gmail.com'
gmail_password = 'fnmf fzhl orcr pxmm'  # Replace with your actual app password

# Email content
from_email = gmail_user
to_email = 'hensonrichard2000@gmail.com'  # Or any test email
subject = 'Test Email via SSL (Port 465)'
body = '✅ This is a test email sent using SSL on port 465.'

# Compose message
msg = MIMEText(body)
msg['Subject'] = subject
msg['From'] = from_email
msg['To'] = to_email

try:
    with smtplib.SMTP_SSL(smtp_server, smtp_port) as server:
        server.login(gmail_user, gmail_password)
        server.send_message(msg)
    print("✅ Email sent successfully using SSL!")
except Exception as e:
    print(f"❌ Failed to send email: {e}")
