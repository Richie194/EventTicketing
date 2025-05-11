from django.db import models

# Existing Event model with enhancements
class Event(models.Model):
    name = models.CharField(max_length=255)
    date_time = models.DateTimeField()
    location = models.CharField(max_length=255)
    normal_price = models.DecimalField(max_digits=10, decimal_places=2)
    vip_price = models.DecimalField(max_digits=10, decimal_places=2)
    vvip_price = models.DecimalField(max_digits=10, decimal_places=2)
    promotion_terms = models.TextField(blank=True, null=True)
    promotion_message = models.TextField(blank=True, null=True)
    banner = models.ImageField(upload_to="event_banners/", blank=True, null=True)
    total_tickets = models.IntegerField(default=0)

    # Enhanced: Adding dynamic remaining tickets calculation
    @property
    def remaining_tickets(self):
        return self.total_tickets - self.tickets.count()

    def __str__(self):
        return self.name

# Enhanced Payment model
class Payment(models.Model):
    event_name = models.CharField(max_length=200)
    ticket_type = models.CharField(max_length=50)
    quantity = models.PositiveIntegerField()
    recipients = models.TextField(help_text="Comma-separated list of recipient emails")
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    buyer_contact = models.CharField(max_length=15)
    buyer_email = models.EmailField(default='example@example.com')  # Default value added here
    payment_method = models.CharField(max_length=20)
    payment_number = models.CharField(max_length=15)
    timestamp = models.DateTimeField(auto_now_add=True)

    # Enhanced: Adding payment status field
    payment_status_choices = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    payment_status = models.CharField(max_length=20, choices=payment_status_choices, default='pending')

    def __str__(self):
        return f"{self.event_name} - {self.payment_method} - {self.payment_number}"

# Enhanced Ticket model
class Ticket(models.Model):
    payment = models.ForeignKey(Payment, on_delete=models.CASCADE, related_name='tickets')
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='tickets')  # added related_name here
    recipient_email = models.EmailField() 
    ticket_type = models.CharField(max_length=50)
    code = models.CharField(max_length=20, unique=True)

    # Enhanced: Adding status and date issued to the ticket
    status_choices = [
        ('active', 'Active'),
        ('used', 'Used'),
        ('expired', 'Expired'),
    ]
    status = models.CharField(max_length=20, choices=status_choices, default='active')
    date_issued = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.code} - {self.recipient_email} - {self.event.name}"

# Enhanced ContactMessage model with status tracking
class ContactMessage(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    subject = models.CharField(max_length=200)
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    # Enhanced: Adding status for message tracking
    status_choices = [
        ('new', 'New'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
    ]
    status = models.CharField(max_length=20, choices=status_choices, default='new')

    def __str__(self):
        return f"Message from {self.name} - {self.email}"

