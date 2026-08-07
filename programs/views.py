

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
    Razorpay redirects here with the exact booking_id in the callback URL.
    The request MUST carry a booking_id — otherwise it is not a genuine
    post-payment redirect and we deny it (no guessing by batch).
    """
    # A valid confirmation must carry the booking_id Razorpay passed back.
    # The booking_id in the URL also survives a manual page refresh.
    booking_id = request.GET.get('booking_id')

    if not booking_id:
        return redirect('/classes/')

    registration = YogaRegistration.objects.filter(booking_id=booking_id).first()

    # The booking must exist AND belong to the batch in the URL
    if not registration or registration.batch != batch_name:
        return redirect('/classes/')

    # Found the exact booking — confirm it.
    registration.status = "Payment Success / Completed"
    registration.save()

    # Clear the session key safely if it exists
    if 'pending_booking_id' in request.session:
        request.session['pending_booking_id'] = None

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