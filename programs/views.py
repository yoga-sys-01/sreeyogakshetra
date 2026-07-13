

# Create your views here.
import json
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import YogaRegistration

@csrf_exempt
def save_registration(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            # Create the record with "Pending" status
            registration = YogaRegistration.objects.create(
                name=data.get('name'),
                phone=data.get('phone'),
                email=data.get('email'),
                batch=data.get('batch'),
                status="Pending" 
            )
            
            # Save the record's unique ID into the browser's temporary session storage
            request.session['pending_booking_id'] = str(registration.booking_id)
            
            return JsonResponse({'status': 'success', 'booking_id': str(registration.booking_id)})
        except Exception as e:
            return JsonResponse({'status': 'failed', 'error': str(e)}, status=400)

# Add this view inside programs/views.py
@csrf_exempt
def accept_terms_api(request, booking_id):
    """Marks the user as agreed to terms and conditions in the database"""
    if request.method == 'POST':
        user_record = get_object_or_404(YogaRegistration, booking_id=booking_id)
        user_record.agreed_to_terms = True
        user_record.save()
        return JsonResponse({'status': 'terms_accepted'})


def payment_success_view(request, batch_name):
    """
    Razorpay redirects here with the batch name string. We look up the latest
    unconfirmed 'Pending' booking for this specific batch and confirm it.
    """
    # 1. Look for the most recent registration matching this batch that hasn't paid yet
    registration = YogaRegistration.objects.filter(batch=batch_name, status="Pending").last()
    
    if registration:
        # 2. Found it! Update their real details (Name, Email, Phone) to completed status
        registration.status = "Payment Success / Completed"
        registration.save()
        
        # Clear the session key safely if it exists
        if 'pending_booking_id' in request.session:
            request.session['pending_booking_id'] = None
    else:
        # 3. Fallback: If no pending row exists, grab the last completed record for this batch
        # so the landing page displays correctly on a manual page refresh.
        registration = YogaRegistration.objects.filter(batch=batch_name, status="Payment Success / Completed").last()
        
        # Emergency fail-safe if your database is completely wiped
        if not registration:
            registration = YogaRegistration.objects.create(
                name="Valued Student",
                phone="0000000000",
                email="student@example.com",
                batch=batch_name,
                status="Payment Success / Completed",
                agreed_to_terms=True
            )
        
    return render(request, 'payment_success.html', {'user': registration})

def whatsapp_redirect_bridge(request, booking_id):
    """Triggered when they click 'Join WhatsApp Group Now' on the success page"""
    user_record = get_object_or_404(YogaRegistration, booking_id=booking_id)
    
    # Map the batch field format to your 4 unique WhatsApp groups
    whatsapp_groups = {
        "morning-600": "https://chat.whatsapp.com/Khj3XdeZPcgIOcCDUE10mZ",
        "morning-715": "https://chat.whatsapp.com/Endoazunz3g5QgQ9n4p19q",
        "morning-830": "https://chat.whatsapp.com/BMVPozajlrCF5dj10vInv0",
        "evening-630": "https://chat.whatsapp.com/Jj3te1vWXwi2qaPo7k6yJC",
    }
    
    target_url = whatsapp_groups.get(user_record.batch, "https://chat.whatsapp.com/DEFAULT_FALLBACK")
    return redirect(target_url)