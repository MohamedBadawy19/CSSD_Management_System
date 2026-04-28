from django.urls import path

from . import views

urlpatterns = [
    path("nurse_create_request/", views.nurse_create_request, name="nurse_create_request"),
    path(
        "save_instrument_request/",
        views.save_instrument_request,
        name="save_instrument_request",
    ),
    path(
        "nurse_request_details/<int:request_id>/",
        views.nurse_request_details,
        name="nurse_request_details",
    ),
]
