from django.urls import path

from . import views

urlpatterns = [
    path("dashboard/", views.dashboard_router, name="dashboard_router"),
    path("nurse_dashboard/", views.nurse_dashboard, name="nurse_dashboard"),
]
