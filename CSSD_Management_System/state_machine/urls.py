from django.urls import path

from . import views

urlpatterns = [
    path(
        "requests/<int:request_id>/mark_collected/",
        views.mark_collected,
        name="mark_collected",
    ),
    path(
        "requests/<int:request_id>/mark_cleaned/",
        views.mark_cleaned,
        name="mark_cleaned",
    ),
    path(
        "requests/<int:request_id>/mark_sterilized/",
        views.mark_sterilized,
        name="mark_sterilized",
    ),
    path(
        "requests/<int:request_id>/mark_packed/",
        views.mark_packed,
        name="mark_packed",
    ),
    path("requests/<int:request_id>/deliver/", views.mark_delivered, name="mark_delivered"),
    path(
        "cssd_request_details/<int:request_id>/",
        views.cssd_request_details,
        name="cssd_request_details",
    ),
    path("nurse_sterile_stock/", views.nurse_sterile_stock, name="nurse_sterile_stock"),
]
