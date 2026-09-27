from django.contrib import admin
from .models import YogaRegistration
from .models import MonthlyRenewal

# Register your models here.
@admin.register(YogaRegistration)
class YogaRegistrationAdmin(admin.ModelAdmin):
    # display the countdown and custom fields in rows
    list_display = ('name', 'phone', 'batch', 'registration_date', 'expiry_date', 'days_remaining', 'agreed_to_terms', 'status')
    
    # Optional bonus: Adds a search bar and a right-hand filter panel to your admin dashboard!
    search_fields = ('name', 'email', 'phone')
    list_filter = ('agreed_to_terms','batch', 'status')
    
@admin.register(MonthlyRenewal)
class MonthlyRenewalAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'batch', 'renewal_month_number','status', 'submitted_at')
    list_filter = ('batch', 'status', 'submitted_at')
    search_fields = ('name', 'phone')
    list_editable = ('status',)  # Allows updating status (Pending/Verified) directly from the list view