import uuid
from .models import Ticket  # Ensure to import your Ticket modelimport qrcode

import qrcode
from io import BytesIO
from django.core.mail import EmailMessage
from django.conf import settings




def generate_ticket_code():
    return str(uuid.uuid4().hex[:8])

def generate_unique_ticket_code():
    while True:
        code = generate_ticket_code()
        if not Ticket.objects.filter(code=code).exists():
            return code




def send_ticket_email_with_qr(ticket):
    data = f"{ticket.code}"
    img = qrcode.make(data)
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)

    email = EmailMessage(
        subject=f"🎟️ Your Ticket for {ticket.event.name}",
        body=f"""
Hi,

You've received a {ticket.ticket_type} ticket for {ticket.event.name}.

🎫 Ticket Code: {ticket.code}
📍 Location: {ticket.event.location}
🕒 Date & Time: {ticket.event.date_time.strftime('%Y-%m-%d %H:%M')}

Please present this code or QR at the entrance.
""",
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[ticket.recipient_email],
    )
    email.attach(f"{ticket.code}.png", buffer.getvalue(), "image/png")
    email.send(fail_silently=False)
