"""
Main URL configuration.
US-07 to US-10 routes are in urls_us07_10.py (Mohamed Badawy).
"""

from django.contrib import admin
from django.urls import path, include
from . import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard_router, name='dashboard_router'),

    # ── Nurse views ───────────────────────────────────────────────
    path('nurse_dashboard/', views.nurse_dashboard, name='nurse_dashboard'),
    path('nurse_create_request/', views.nurse_create_request, name='nurse_create_request'),
    path('save_instrument_request/', views.save_instrument_request, name='save_instrument_request'),
    path('nurse_request_details/<int:request_id>/', views.nurse_request_details, name='nurse_request_details'),

    # ── US-07 to US-10 (Mohamed Badawy) — see urls_us07_10.py ────
    path('', include('CSSD_Management_System.urls_us07_10')),
]
