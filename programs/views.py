

# Create your views here.
import json
from urllib.parse import parse_qs
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import YogaRegistration
from .models import MonthlyRenewal

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
    Razorpay Payment Buttons redirect here after payment. The redirect URL is
    configured per button in the Razorpay Dashboard (one URL per batch), and
    Razorpay appends a genuine payment id to it. Its presence is our proof that
    a real payment redirect happened.

    We then confirm the exact booking stored in this browser's session when the
    user registered — never "the latest pending row for the batch".
    """
    # A real post-payment redirect from Razorpay always carries a payment id.
    # Direct visits to this URL (no payment) will not have it and are denied.

    # Collect the query params. Razorpay sometimes appends the extra params with
    # "?" instead of "&" (e.g. `?booking_id=abc?razorpay_payment_id=pay_...`),
    # which would otherwise swallow the payment id inside the booking_id value.
    # Normalise the query string before reading it.
    params = {
        k: v[0]
        for k, v in parse_qs(request.META.get('QUERY_STRING', '').replace('?', '&')).items()
    }

    # Payment button callbacks may also arrive as a POST body.
    if request.method == 'POST':
        for key, value in request.POST.items():
            params[key] = value

    # A genuine redirect from Razorpay carries at least one of these markers.
    # (Payment Buttons do not always include razorpay_payment_id.)
    is_razorpay_redirect = any(
        params.get(k)
        for k in (
            'razorpay_payment_id',
            'razorpay_payment_link_id',
            'razorpay_payment_link_reference_id',
            'razorpay_signature',
        )
    )

    booking_id = (
        params.get('booking_id')
        or params.get('razorpay_payment_link_reference_id')
        or request.session.get('pending_booking_id')
    )

    if not booking_id:
        return redirect('/classes/')

    registration = YogaRegistration.objects.filter(booking_id=booking_id).first()

    # The booking must exist AND belong to the batch in the URL
    if not registration or registration.batch != batch_name:
        return redirect('/classes/')

    # Only accept the redirect if Razorpay sent us a marker, or this browser
    # actually created the booking (session proof) — not random direct visits.
    session_matches = request.session.get('pending_booking_id') == booking_id
    if not (is_razorpay_redirect or session_matches):
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
        "morning-1030":"https://chat.whatsapp.com/K9GrQ92hpLTHgIwavbNMUh?s=cl&p=a&mlu=4&ilr=4",
    }
    
    target_url = whatsapp_groups.get(user_record.batch, "https://chat.whatsapp.com/DEFAULT_FALLBACK")
    return redirect(target_url)

@csrf_exempt
def submit_renewal_api(request):
    """Handles GPay payment confirmation submission"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            renewal = MonthlyRenewal.objects.create(
                name=data.get('name'),
                phone=data.get('phone'),
                batch=data.get('batch'),
                renewal_month_number=int(data.get('renewal_month_number', 2)),
                status="Pending Verification"
            )
            return JsonResponse({'status': 'success', 'message': 'Renewal request submitted successfully!'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)