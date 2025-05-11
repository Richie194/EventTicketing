from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib.auth import authenticate, login as auth_login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from .models import Payment, Event, Ticket
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from .paystack import Paystack
from django.conf import settings
from django.core.mail import send_mail
from .utils import generate_ticket_code
from collections import defaultdict
from django.db.models import Count
from decimal import Decimal
from django.core.serializers.json import DjangoJSONEncoder
import json
from .models import ContactMessage  # Import the model
from django.contrib import messages  # For success feedback
from django.contrib import messages as django_messages
from home.models import Ticket
from .utils import send_ticket_email_with_qr
from django.db.models import Sum
import pandas as pd
from django.template.loader import get_template
from xhtml2pdf import pisa

from django.db.models import Case, When, Value, IntegerField
from django.db.models import  DecimalField, Q
from django.db.models.functions import Coalesce



TEMPLATE_DIRS = (
    'os.path.join(BASE-DIR, "templates")'
)

# Public pages
def myindex(request):
    events = Event.objects.all()  # Or filter as needed
    return render(request, "home/myindex.html", {"events": events})


def about(request):
    return render(request, "home/about.html")


def contact(request):
    if request.method == "POST":
        name = request.POST.get("name")
        email = request.POST.get("email")
        subject = request.POST.get("subject")
        message = request.POST.get("message")

        ContactMessage.objects.create(
            name=name,
            email=email,
            subject=subject,
            message=message
        )
        return render(request, "home/contact.html", {"success": True})

    return render(request, "home/contact.html")

def view_contact_messages(request):
    messages = ContactMessage.objects.all().order_by('-timestamp')
    return render(request, 'home/view_contacts.html', {'messages': messages})


def service(request):
    return render(request, 'home/service.html')

def portfolio(request):
    return render(request, 'home/portfolio.html')

def pricing(request):
    events = Event.objects.all()  # Fetch all events
    print(events)  # Debug: Check if events are retrieved
    return render(request, 'home/pricing.html', {'events': events})


def skill(request):
    return render(request, 'home/skill.html')

def team(request):
    return render(request, 'home/team.html')

def review(request):
    return render(request, 'home/review.html')

def client(request):
    return render(request, 'home/client.html')

def single(request):
    return render(request, 'home/single.html')


    # ---- ADMIN------
def index2(request):
    return render(request, 'home/index2.html', context)
def index(request):
    return render(request, 'home/index.html')





def charts(request):
    try:
        # 1. Get ticket counts with null protection
        ticket_counts = Ticket.objects.aggregate(
            normal=Coalesce(Count('id', filter=Q(ticket_type='Normal')), 0),
            vip=Coalesce(Count('id', filter=Q(ticket_type='VIP')), 0),
            vvip=Coalesce(Count('id', filter=Q(ticket_type='VVIP')), 0)
        )

        # Debug output
        print(f"Raw ticket counts: {ticket_counts}")

        # 2. Calculate revenue by event with null protection
        events_with_revenue = Event.objects.annotate(
            revenue=Coalesce(
                Sum(
                    Case(
                        When(tickets__ticket_type='Normal', then='normal_price'),
                        When(tickets__ticket_type='VIP', then='vip_price'),
                        When(tickets__ticket_type='VVIP', then='vvip_price'),
                        default=Value(Decimal('0.00')),
                        output_field=DecimalField()
                    )
                ),
                Value(Decimal('0.00'))
            )
        ).filter(revenue__gt=0).order_by('-revenue')[:10]  # Limit to top 10

        print(f"Found {len(events_with_revenue)} events with revenue")

        # 3. Prepare safe event data
        event_data = []
        for event in events_with_revenue:
            try:
                event_data.append({
                    'name': event.name[:20] if event.name else 'Unnamed Event',
                    'revenue': float(event.revenue) if event.revenue else 0.0
                })
            except Exception as e:
                print(f"Error processing event {event.id}: {str(e)}")
                continue

        # 4. Prepare context with multiple data checks
        has_tickets = any(ticket_counts.values())
        has_events = bool(event_data)
        total_tickets = sum(ticket_counts.values())
        total_revenue = sum(item['revenue'] for item in event_data)

        context = {
            # Raw counts
            'normal_count': int(ticket_counts['normal']),
            'vip_count': int(ticket_counts['vip']),
            'vvip_count': int(ticket_counts['vvip']),
            
            # JSON data
            'event_revenue_json': json.dumps(event_data, cls=DjangoJSONEncoder),
            'event_names_json': json.dumps([e['name'] for e in event_data]),
            'event_revenues_json': json.dumps([e['revenue'] for e in event_data]),
            
            # Aggregates
            'total_tickets': total_tickets,
            'total_revenue': total_revenue,
            'event_count': len(event_data),
            
            # Data flags
            'has_data': has_tickets or has_events,  # Show if either exists
            'has_tickets': has_tickets,
            'has_events': has_events,
            
            # Debug info
            'debug_ticket_counts': ticket_counts,
            'debug_event_count': len(event_data)
        }

        print(f"Context prepared: { {k: v for k, v in context.items() if not k.startswith('debug_')} }")

    except Exception as e:
        print(f"Error in charts view: {str(e)}")
        context = {
            'normal_count': 0,
            'vip_count': 0,
            'vvip_count': 0,
            'event_revenue_json': '[]',
            'event_names_json': '[]',
            'event_revenues_json': '[]',
            'total_tickets': 0,
            'total_revenue': 0.0,
            'event_count': 0,
            'has_data': False,
            'has_tickets': False,
            'has_events': False,
            'error': str(e)
        }

    return render(request, 'home/charts.html', context)
    

def forgotPassword(request):
    return render(request, 'home/forgotPassword.html')



# --------- CREATE EVENTS ----------
# Create Event View

def create_event(request):
    if request.method == "POST":
        event_name = request.POST.get("eventName")
        event_date_time = request.POST.get("eventDateTime")
        event_location = request.POST.get("eventLocation")

        ticket_normal = request.POST.get("ticketNormal", "0").replace("GHS", "").strip()
        ticket_vip = request.POST.get("ticketVIP", "0").replace("GHS", "").strip()
        ticket_vvip = request.POST.get("ticketVVIP", "0").replace("GHS", "").strip()

        promotion_terms = request.POST.get("promotionTerms", "")
        promotion_message = request.POST.get("promotionMessage", "")
        event_banner = request.FILES.get("eventBanner")

        total_tickets = request.POST.get("totalTickets")

        # Validation
        if not event_name:
            messages.error(request, "Event name is required.")
            return redirect("create_event")

        try:
            ticket_normal = float(ticket_normal) if ticket_normal else 0.0
            ticket_vip = float(ticket_vip) if ticket_vip else 0.0
            ticket_vvip = float(ticket_vvip) if ticket_vvip else 0.0
        except ValueError:
            messages.error(request, "Invalid price format. Please enter numbers only (e.g., 30.4).")
            return redirect("create_event")

        if not total_tickets or not total_tickets.isdigit():
            messages.error(request, "Please enter a valid number of tickets.")
            return redirect("create_event")
        total_tickets = int(total_tickets)

        # Save event
        event = Event.objects.create(
            name=event_name,
            date_time=event_date_time,
            location=event_location,
            normal_price=ticket_normal,
            vip_price=ticket_vip,
            vvip_price=ticket_vvip,
            promotion_terms=promotion_terms,
            promotion_message=promotion_message,
            banner=event_banner,
            total_tickets=total_tickets,
        )

        messages.success(request, "Event created successfully!")
        return redirect("create_event")

    return render(request, "home/create_event.html")


    #  ---------- UPDATE EVENTS --------
   
def update_event_list(request):
    events = Event.objects.all()
    return render(request, "home/update_event_list.html", {"events": events})


def edit_event(request, event_id):
    event = get_object_or_404(Event, id=event_id)

    if request.method == "POST":
        event.name = request.POST.get("eventName")
        event.date_time = request.POST.get("eventDateTime")
        event.location = request.POST.get("eventLocation")

        event.normal_price = request.POST.get("ticketNormal")
        event.vip_price = request.POST.get("ticketVIP")
        event.vvip_price = request.POST.get("ticketVVIP")

        event.promotion_terms = request.POST.get("promotionTerms")
        event.promotion_message = request.POST.get("promotionMessage")
        event.total_tickets = request.POST.get("totalTickets")

        if "eventBanner" in request.FILES:
            event.banner = request.FILES["eventBanner"]

        event.save()
        messages.success(request, "Event updated successfully!")
        return redirect("update_event_list")

    return render(request, "home/edit_event.html", {"event": event})

#  ------- DELETE ---------
def delete_event(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    event.delete()
    messages.success(request, "Event deleted successfully.")
    return redirect('update_event_list')  # Redirect back to the event list

# ------ REGISTRATION ------------
def register(request):
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        username = request.POST.get('username')
        email = request.POST.get('email')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')

        if password1 != password2:
            messages.error(request, "Passwords do not match!")
            return redirect('register')

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already taken!")
            return redirect('register')

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already in use!")
            return redirect('register')

        user = User.objects.create_user(username=username, email=email, password=password1)
        user.first_name = first_name
        user.last_name = last_name
        user.save()

        messages.success(request, "Account created successfully! You can now log in.")
        return redirect('login')

    return render(request, 'home/register.html')




# ✅ LOGIN VIEW with authentication
def login_view(request):
    if request.method == 'POST':
        identifier = request.POST.get('username')  # This can be username or email
        password = request.POST.get('password')

        # Check if user entered an email instead of a username
        try:
            user = User.objects.get(email=identifier)
            username = user.username  # Convert email to username
        except User.DoesNotExist:
            username = identifier  # Assume it's a username

        user = authenticate(request, username=username, password=password)
        if user is not None:
            auth_login(request, user)
            return redirect('index2')
        else:
            messages.error(request, "Invalid username/email or password")
            return redirect('login')

    return render(request, 'home/login.html')


# ✅ Protect index2 (Admin Dashboard) - Only logged-in users
@login_required(login_url='login')
def index2(request):
    return render(request, 'home/index2.html')

# ✅ Logout view
def logout_view(request):
    logout(request)
    return redirect('login')



# --------- BUY TICKETS --------

# View to display the ticket form
def buyTicket(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    return render(request, 'home/buyTicket.html', {'event': event})



# Process the ticket order


def process_ticket_order(request, event_id):
    if request.method == 'POST':
        ticket_type = request.POST.get('ticket_type')
        quantity = request.POST.get('quantity')
        buyer_contact = request.POST.get('buyer_contact')
        buyer_email = request.POST.get('buyer_email')
        payment_method = request.POST.get('payment_method')
        payment_number = request.POST.get('payment_number')
        delivery_option = request.POST.get('delivery_option')  # 👈 get which delivery method was chosen

        # Validate quantity
        try:
            quantity = int(quantity)
        except (TypeError, ValueError):
            messages.error(request, "Please enter a valid quantity.")
            return redirect('buyTicket', event_id=event_id)

        # Fetch event
        event = get_object_or_404(Event, id=event_id)

        # Calculate total price
        ticket_type_lower = ticket_type.lower()
        if ticket_type_lower == 'normal':
            total_price = event.normal_price * quantity
        elif ticket_type_lower == 'vip':
            total_price = event.vip_price * quantity
        elif ticket_type_lower == 'vvip':
            total_price = event.vvip_price * quantity
        else:
            messages.error(request, "Invalid ticket type selected.")
            return redirect('buyTicket', event_id=event_id)

        # Generate a unique ticket code
        ticket_code = generate_ticket_code()

        # 🔁 Handle recipients logic
        recipients = []
        if delivery_option == 'main':
            # 👇 all tickets go to buyer's email
            recipients = [buyer_email] * quantity
        else:
            # 👇 send each ticket to individual email; get from input
            other_emails = request.POST.getlist('recipients')
            recipients = [buyer_email] + other_emails  # first ticket goes to buyer, rest from form

            # Ensure number of emails matches quantity
            if len(recipients) != quantity:
                messages.error(request, "Please enter email addresses for all recipients.")
                return redirect('buyTicket', event_id=event_id)

        # Store everything in session to pass to payment view
        request.session['payment_data'] = {
            'event_id': event.id,
            'event_name': event.name,
            'ticket_type': ticket_type,
            'quantity': quantity,
            'buyer_contact': buyer_contact,
            'buyer_email': buyer_email,
            'payment_method': payment_method,
            'payment_number': payment_number,
            'delivery_option': delivery_option,
            'recipients': recipients,
            'total_price': float(total_price),
            'ticket_code': ticket_code,
        }

        return redirect('purchase_info', event_id=event_id)

    return redirect('buyTicket', event_id=event_id)






def purchase_info(request, event_id):
    payment_data = request.session.get('payment_data')
    if not payment_data:
        return redirect('pricing')

    context = {
        'event_id': event_id,
        'event_name': payment_data.get('event_name'),
        'ticket_type': payment_data.get('ticket_type'),
        'quantity': payment_data.get('quantity'),
        'buyer_contact': payment_data.get('buyer_contact'),
        'buyer_email': payment_data.get('buyer_email'),  
        'total_price': payment_data.get('total_price'),
        'recipients': payment_data.get('recipients'),
        'paystack_public_key': settings.PAYSTACK_PUBLIC_KEY  # ✅ include this!
    }
    return render(request, 'home/purchase_info.html', context)








@csrf_exempt
def confirm_payment(request):
    payment_data = request.session.get('payment_data')

    if not payment_data:
        messages.error(request, "Payment session expired or invalid.")
        return redirect('pricing')

    try:
        event = get_object_or_404(Event, id=payment_data['event_id'])

        # Validate required fields
        required_fields = ['ticket_type', 'quantity', 'recipients', 'total_price', 'buyer_contact', 'buyer_email', 'payment_method', 'payment_number']
        for field in required_fields:
            if not payment_data.get(field):
                messages.error(request, f"Missing payment info: {field}")
                return redirect('buyTicket', event_id=event.id)

        # Save Payment
        payment = Payment.objects.create(
            event_name=event.name,
            ticket_type=payment_data['ticket_type'],
            quantity=payment_data['quantity'],
            recipients=','.join(payment_data['recipients']),
            total_price=payment_data['total_price'],
            buyer_contact=payment_data['buyer_contact'],
            buyer_email=payment_data['buyer_email'],
            payment_method=payment_data['payment_method'],
            payment_number=payment_data['payment_number'],
        )

        # Generate and email tickets
        ticket_codes = []
        recipient_emails = [payment_data['buyer_email']] * payment_data['quantity'] if payment_data['quantity'] == 1 or payment_data['delivery_option'] == 'main' else payment_data['recipients']

        for recipient in recipient_emails:
            code = generate_unique_ticket_code()
            ticket = Ticket.objects.create(
                payment=payment,
                event=event,
                recipient_email=recipient,
                ticket_type=payment.ticket_type,
                code=code,
            )
            ticket_codes.append((recipient, code))

            # Send ticket via email
            send_ticket_email_with_qr(ticket)

        # Buyer summary email
        codes_formatted = "\n".join(f"{email}: {code}" for email, code in ticket_codes)
        subject = f"🎟️ Ticket Purchase Confirmation for {event.name}"
        message = f"""
Hi there,

Thanks for purchasing {payment.quantity} {payment.ticket_type} ticket(s) for {event.name}.

Event: {event.name}
Location: {event.location}
Date & Time: {event.date_time.strftime('%Y-%m-%d %H:%M')}
Ticket Type: {payment.ticket_type}
Quantity: {payment.quantity}
Total Paid: {payment.total_price}
Contact: {payment.buyer_contact}

🎫 Ticket Code(s):
{codes_formatted}

Inform your guests to bring their ticket codes to the event.
"""
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [payment.buyer_email], fail_silently=False)

        del request.session['payment_data']
        return render(request, 'success.html', {'payment': payment})

    except Exception as e:
        messages.error(request, f"An error occurred: {str(e)}")
        return redirect('buyTicket', event_id=payment_data.get('event_id', ''))





def verify_payment(request, event_id):
    reference = request.GET.get('reference')
    payment_data = request.session.get('payment_data')

    if reference and payment_data:
        verified = Paystack.verify_payment(reference, float(payment_data['total_price']))
        if verified:
            event = get_object_or_404(Event, id=event_id)

            payment = Payment.objects.create(
                event_name=payment_data['event_name'],
                ticket_type=payment_data['ticket_type'],
                quantity=payment_data['quantity'],
                recipients=','.join(payment_data.get('recipients', [])),
                total_price=payment_data['total_price'],
                buyer_contact=payment_data['buyer_contact'],
                buyer_email=payment_data['buyer_email'],
                payment_method='Paystack',
                payment_number=payment_data['buyer_contact'],
            )

            ticket_codes = []
            recipient_emails = [payment_data['buyer_email']] * payment_data['quantity'] if payment_data['quantity'] == 1 or payment_data['delivery_option'] == 'main' else payment_data['recipients']

            for recipient in recipient_emails:
                code = generate_ticket_code()
                ticket = Ticket.objects.create(
                    payment=payment,
                    event=event,
                    recipient_email=recipient,
                    ticket_type=payment.ticket_type,
                    code=code,
                )
                ticket_codes.append((recipient, code))

                # Send ticket via email
                send_ticket_email_with_qr(ticket)

            codes_formatted = "\n".join(f"{email}: {code}" for email, code in ticket_codes)
            subject = f"🎟️ Ticket Confirmation for {event.name}"
            message = f"""
Hi there,

Thanks for purchasing {payment.quantity} {payment.ticket_type} ticket(s) for {event.name}.

Event: {event.name}
Location: {event.location}
Date & Time: {event.date_time.strftime('%Y-%m-%d %H:%M')}
Ticket Type: {payment.ticket_type}
Quantity: {payment.quantity}
Total Paid: GHS {payment.total_price}
Contact: {payment.buyer_contact}

🎫 Ticket Code(s):
{codes_formatted}

Inform your guests to bring their ticket codes to the event.
"""
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [payment.buyer_email], fail_silently=False)

            del request.session['payment_data']
            return render(request, "home/payment_success.html", {'payment': payment})
        else:
            messages.error(request, "Payment verification failed!")

    return redirect('pricing')


from django.shortcuts import render
from django.db.models import Sum, Count, Case, When, Value, DecimalField
from decimal import Decimal
from collections import defaultdict
from .models import Ticket, Event

def all_tickets_view(request):
    event_id = request.GET.get('event')
    email_query = request.GET.get('email')
    
    # Base queryset
    tickets = Ticket.objects.select_related('event').all().order_by('-id')
    events = Event.objects.all()
    
    # Apply filters
    if event_id:
        tickets = tickets.filter(event__id=event_id)
    
    if email_query:
        tickets = tickets.filter(recipient_email__icontains=email_query)
    
    # Get ticket counts by type
    ticket_counts = (
        Ticket.objects.values('event__id', 'ticket_type')
        .annotate(count=Count('id')))
    
    # Convert to dictionary format
    count_dict = defaultdict(lambda: {"Normal": 0, "VIP": 0, "VVIP": 0})
    for item in ticket_counts:
        count_dict[item['event__id']][item['ticket_type']] = item['count']
    
    # Build ticket summary per event
    ticket_stats = []
    for event in events:
        sold = count_dict[event.id]
        total = event.total_tickets or 0
        
        # Calculate tickets left
        total_sold = sold["Normal"] + sold["VIP"] + sold["VVIP"]
        tickets_left = max(0, total - total_sold)
        
        ticket_stats.append({
            "event": event.name,
            "normal_sold": sold["Normal"],
            "vip_sold": sold["VIP"],
            "vvip_sold": sold["VVIP"],
            "tickets_left": tickets_left,
            "total": total
        })
    
    # Calculate totals using aggregation
    revenue_data = tickets.aggregate(
        total_revenue=Sum(
            Case(
                When(ticket_type='Normal', then='event__normal_price'),
                When(ticket_type='VIP', then='event__vip_price'),
                When(ticket_type='VVIP', then='event__vvip_price'),
                default=Value(Decimal('0.00')),
                output_field=DecimalField()
            )
        ),
        total_tickets=Count('id')
    )
    
    # Calculate revenue per event
    event_revenue = (
        tickets.values('event__name')
        .annotate(
            revenue=Sum(
                Case(
                    When(ticket_type='Normal', then='event__normal_price'),
                    When(ticket_type='VIP', then='event__vip_price'),
                    When(ticket_type='VVIP', then='event__vvip_price'),
                    default=Value(Decimal('0.00')),
                    output_field=DecimalField()
                )
            )
        )
    )
    
    context = {
        'tickets': tickets,
        'events': events,
        'selected_event': event_id,
        'email_query': email_query,
        'ticket_stats': ticket_stats,
        'total_revenue': revenue_data['total_revenue'] or Decimal('0.00'),
        'total_tickets_sold': revenue_data['total_tickets'],
        'event_revenue': {item['event__name']: item['revenue'] or Decimal('0.00') 
                         for item in event_revenue},
    }
    
    return render(request, 'home/all_tickets.html', context)


    # verify_ticket_code

def verify_ticket(request):
    if request.method == 'POST':
        code = request.POST.get('code')
        try:
            ticket = Ticket.objects.get(code=code)
            if ticket.status == 'used':
                status = "This ticket has already been used."
                color = "danger"
            elif ticket.status == 'expired':
                status = "This ticket has expired."
                color = "warning"
            else:
                ticket.status = 'used'  # Mark it as used
                ticket.save()
                status = "Ticket is valid and now marked as used."
                color = "success"
        except Ticket.DoesNotExist:
            ticket = None
            status = "Ticket code not found."
            color = "warning"

        return render(request, 'home/verify_ticket.html', {
            'ticket': ticket,
            'status': status,
            'color': color,
        })

    return render(request, 'home/verify_ticket.html')








def revenue_chart_view(request):
    print("DEBUG: Starting revenue chart view processing")

    tickets = Ticket.objects.select_related('event').all()
    print(f"DEBUG: Found {tickets.count()} tickets")

    revenue_data = defaultdict(lambda: {"Normal": Decimal('0.00'), "VIP": Decimal('0.00'), "VVIP": Decimal('0.00')})

    for ticket in tickets:
        event = ticket.event
        print(f"DEBUG: Ticket for event {event.name}, type {ticket.ticket_type}")
        if ticket.ticket_type == "Normal":
            revenue_data[event.name]["Normal"] += event.normal_price
        elif ticket.ticket_type == "VIP":
            revenue_data[event.name]["VIP"] += event.vip_price
        elif ticket.ticket_type == "VVIP":
            revenue_data[event.name]["VVIP"] += event.vvip_price

    # Convert Decimal to float for JSON serialization
    cleaned_revenue = {
        event_name: {
            "Normal": float(data["Normal"]),
            "VIP": float(data["VIP"]),
            "VVIP": float(data["VVIP"]),
        }
        for event_name, data in revenue_data.items()
    }

    print("DEBUG: Final cleaned revenue data:", cleaned_revenue)

    context = {
        'event_revenue_json': json.dumps(cleaned_revenue),
        'currency_symbol': 'GHS'
    }

    return render(request, 'home/charts.html', context)





def delete_message(request, pk):
    msg = get_object_or_404(ContactMessage, pk=pk)
    msg.delete()
    django_messages.success(request, "Message deleted successfully.")
    return redirect('view_contact_messages')  # replace with your actual view name



#  REPORT GENERATING

def report_view(request):
    report_data = []
    total_normal_revenue = 0
    total_vip_revenue = 0
    total_vvip_revenue = 0
    total_sold = 0

    events = Event.objects.all()
    for event in events:
        # Fetch tickets by type
        normal_tickets = event.tickets.filter(ticket_type='Normal').count()
        vip_tickets = event.tickets.filter(ticket_type='VIP').count()
        vvip_tickets = event.tickets.filter(ticket_type='VVIP').count()

        # Revenue calculations
        normal_revenue = normal_tickets * float(event.normal_price)
        vip_revenue = vip_tickets * float(event.vip_price)
        vvip_revenue = vvip_tickets * float(event.vvip_price)
        total_revenue = normal_revenue + vip_revenue + vvip_revenue

        # Accumulate overall totals
        total_normal_revenue += normal_revenue
        total_vip_revenue += vip_revenue
        total_vvip_revenue += vvip_revenue
        total_sold += normal_tickets + vip_tickets + vvip_tickets

        report_data.append({
            'event': event,
            'normal_tickets': normal_tickets,
            'vip_tickets': vip_tickets,
            'vvip_tickets': vvip_tickets,
            'normal_revenue': normal_revenue,
            'vip_revenue': vip_revenue,
            'vvip_revenue': vvip_revenue,
            'total_revenue': total_revenue,
            'total_sold': normal_tickets + vip_tickets + vvip_tickets,
            'remaining': event.remaining_tickets,
        })

    overall = {
        'total_sold': total_sold,
        'normal_revenue': total_normal_revenue,
        'vip_revenue': total_vip_revenue,
        'vvip_revenue': total_vvip_revenue,
        'total_revenue': total_normal_revenue + total_vip_revenue + total_vvip_revenue
    }

    return render(request, 'home/report.html', {
        'report_data': report_data,
        'overall': overall
    })




def download_excel(request):
    events = Event.objects.all()

    data = []
    overall = {
        'total_sold': 0,
        'normal_revenue': 0,
        'vip_revenue': 0,
        'vvip_revenue': 0,
        'total_revenue': 0,
    }

    for event in events:
        normal_tickets = Ticket.objects.filter(event=event, ticket_type='Normal').count()
        vip_tickets = Ticket.objects.filter(event=event, ticket_type='VIP').count()
        vvip_tickets = Ticket.objects.filter(event=event, ticket_type='VVIP').count()

        normal_revenue = normal_tickets * event.normal_price
        vip_revenue = vip_tickets * event.vip_price
        vvip_revenue = vvip_tickets * event.vvip_price

        total_sold = normal_tickets + vip_tickets + vvip_tickets
        total_revenue = normal_revenue + vip_revenue + vvip_revenue
        remaining = event.total_tickets - total_sold

        data.append({
            'Event': event.name,
            'Date': event.date_time.strftime('%Y-%m-%d %H:%M'),
            'Normal Tickets': normal_tickets,
            'VIP Tickets': vip_tickets,
            'VVIP Tickets': vvip_tickets,
            'Total Sold': total_sold,
            'Remaining': remaining,
            'Normal Revenue': normal_revenue,
            'VIP Revenue': vip_revenue,
            'VVIP Revenue': vvip_revenue,
            'Total Revenue': total_revenue,
        })

        overall['total_sold'] += total_sold
        overall['normal_revenue'] += normal_revenue
        overall['vip_revenue'] += vip_revenue
        overall['vvip_revenue'] += vvip_revenue
        overall['total_revenue'] += total_revenue

    df = pd.DataFrame(data)

    # Add overall totals row
    df.loc[len(df.index)] = [
        'TOTALS', '', '', '', '',
        overall['total_sold'], '', 
        overall['normal_revenue'],
        overall['vip_revenue'],
        overall['vvip_revenue'],
        overall['total_revenue']
    ]

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=report.xlsx'
    with pd.ExcelWriter(response, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Report')

    return response



def download_pdf(request):
    events = Event.objects.all()
    report_data = []
    overall = {
        'total_sold': 0,
        'normal_revenue': 0,
        'vip_revenue': 0,
        'vvip_revenue': 0,
        'total_revenue': 0,
    }

    for event in events:
        normal_tickets = Ticket.objects.filter(event=event, ticket_type='Normal').count()
        vip_tickets = Ticket.objects.filter(event=event, ticket_type='VIP').count()
        vvip_tickets = Ticket.objects.filter(event=event, ticket_type='VVIP').count()

        normal_revenue = normal_tickets * event.normal_price
        vip_revenue = vip_tickets * event.vip_price
        vvip_revenue = vvip_tickets * event.vvip_price

        total_sold = normal_tickets + vip_tickets + vvip_tickets
        total_revenue = normal_revenue + vip_revenue + vvip_revenue
        remaining = event.total_tickets - total_sold

        report_data.append({
            'event': event,
            'normal_tickets': normal_tickets,
            'vip_tickets': vip_tickets,
            'vvip_tickets': vvip_tickets,
            'total_sold': total_sold,
            'remaining': remaining,
            'normal_revenue': normal_revenue,
            'vip_revenue': vip_revenue,
            'vvip_revenue': vvip_revenue,
            'total_revenue': total_revenue,
        })

        overall['total_sold'] += total_sold
        overall['normal_revenue'] += normal_revenue
        overall['vip_revenue'] += vip_revenue
        overall['vvip_revenue'] += vvip_revenue
        overall['total_revenue'] += total_revenue

    context = {
        'report_data': report_data,
        'overall': overall
    }

    template = get_template('home/report_pdf.html')
    html = template.render(context)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="report.pdf"'
    pisa.CreatePDF(html, dest=response)
    return response

