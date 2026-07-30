"""
URL configuration for website project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.conf import settings             # <-- ADD THIS LINE
from django.conf.urls.static import static
from . import views
from programs import views as program_views
from django.views.generic import TemplateView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('',views.home),
    path('about/',views.about),
    path('classes/',views.classes),
    path('gallery/',views.gallery),
    path('contact/',views.contact),

    path('api/save-registration/', program_views.save_registration, name='save_registration'),
    
    # Matches: /payment-success/morning-6/
    path('payment-success/<str:batch_name>/', program_views.payment_success_view, name='payment_success_page'),
    
    # Tracking button destination
    path('join-group/<str:booking_id>/', program_views.whatsapp_redirect_bridge, name='whatsapp_bridge'),

    # Add this line alongside your other paths:
    path('api/accept-terms/<str:booking_id>/', program_views.accept_terms_api, name='accept_terms_api'),


    path(
        "robots.txt",
        TemplateView.as_view(
            template_name="robots.txt", content_type="text/plain"
        ),
    ),

]


# Add this block at the very end of the file:
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
