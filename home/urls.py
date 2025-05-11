from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static
from .views import delete_event
from home.views import verify_ticket
from .views import report_view

from .views import report_view, download_excel
from .views import download_pdf


urlpatterns = [
    path('', views.myindex, name='myindex'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('service/', views.service, name='service'),
    path('portfolio/', views.portfolio, name='portfolio'),
    path('pricing/', views.pricing, name='pricing'),
    path('skill/', views.skill, name='skill'),
    path('team/', views.team, name='team'),
    path('review/', views.review, name='review'),
    path('client/', views.client, name='client'),
    path('single/', views.single, name='single'),
   

    # -----------ADMINS-----------
    path('index/', views.index, name='index'),
    path('index2/', views.index2, name='index2'),  # Admin dashboard (protected)
    path('charts/', views.charts, name='charts'),
    path('login/', views.login_view, name='login'),  # Login route
    path('logout/', views.logout_view, name='logout'),
    path('forgotPassword/', views.forgotPassword, name='forgotPassword'),
    path('register/', views.register, name='register'),
    
    
        # ------- CREATE EVENT ----------
    path('create_event/', views.create_event, name='create_event'),
    path('update_event/', views.update_event_list, name='update_event_list'),
    path('edit_event/<int:event_id>/', views.edit_event, name='edit_event'),

    path('delete_event/<int:event_id>/', delete_event, name='delete_event'),
   

    # ---------- BUY TICKETS -------
    path('buy-ticket/<int:event_id>/', views.buyTicket, name='buyTicket'),  # Display the form
    path('buy-ticket/<int:event_id>/process/', views.process_ticket_order, name='process_ticket_order'),  # Handle form submission

    path('confirm_payment/', views.confirm_payment, name='confirm_payment'),
    path('purchase_info/<int:event_id>/', views.purchase_info, name='purchase_info'),
   
    path('verify_payment/<int:event_id>/', views.verify_payment, name='verify_payment'),
    path('all-tickets/', views.all_tickets_view, name='all_tickets'),

    path('charts/', views.revenue_chart_view, name='revenue_chart'),

    path("dashboard/messages/", views.view_contact_messages, name="view_contact_messages"),
    path('delete-message/<int:pk>/', views.delete_message, name='delete_message'),

    path('verify-ticket/', verify_ticket, name='verify_ticket'),
    path('report/', report_view, name='report'),

    path('report/download/excel/', views.download_excel, name='download_excel'),
    path('report/download/pdf/', download_pdf, name='download_pdf'),


]

# This ensures that Django serves uploaded media files only in devel
# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

