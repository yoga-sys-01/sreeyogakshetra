from django.db import models

# Create your models here.
import uuid
from django.utils import timezone
from datetime import timedelta

class YogaRegistration(models.Model):
    BATCH_CHOICES = [
        ('morning-600', 'Morning: 6:00 AM – 7:00 AM'),
        ('morning-715', 'Morning: 7:15 AM – 8:15 AM'),
        ('morning-830', 'Morning: 8:30 AM – 9:30 AM'),
        ('morning-1030', 'Morning: 10:30 AM – 11:30 AM'),
    ]

    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15)
    email = models.EmailField()
    batch = models.CharField(max_length=20, choices=BATCH_CHOICES)
    registration_date = models.DateTimeField(default=timezone.now)
    
    # We remove the hardcoded default calculation here to prevent global server time locking
    expiry_date = models.DateTimeField(blank=True, null=True)
    
    booking_id = models.CharField(max_length=100, unique=True, default=uuid.uuid4, editable=False)
    status = models.CharField(max_length=50, default="Pending")
    agreed_to_terms = models.BooleanField(default=False) 

    @property
    def days_remaining(self):
        """Calculates days left only if payment status is Success / Completed"""
        if self.status != "Payment Success / Completed":
            return "-"  # Returns a clean dash in the admin panel if not paid
            
        if self.expiry_date:
            # We look at the date difference dynamically
            remaining = self.expiry_date - timezone.now()
            return max(0, remaining.days)
            
        return 0

    def save(self, *args, **kwargs):
        """Automatically calculates a dynamic 30 days expiry date when first saved"""
        if not self.expiry_date:
            self.expiry_date = timezone.now() + timedelta(days=30)
        super(YogaRegistration, self).save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} - {self.batch}"
    
class MonthlyRenewal(models.Model):
    BATCH_CHOICES = YogaRegistration.BATCH_CHOICES

    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15)
    batch = models.CharField(max_length=20, choices=BATCH_CHOICES)
    renewal_month_number = models.CharField(max_length=50, default="2nd Month")
    
    submitted_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=50, default="Pending Verification")

    def __str__(self):
        return f"{self.name} - Month {self.renewal_month_number} Renewal ({self.batch})"