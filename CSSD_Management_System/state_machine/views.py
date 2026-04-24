from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from department_requests.models import (
    InstrumentRequest,
    Notification,
    RequestItem,
)

from .models import SterilizationBatch


def _detail_context(instrument_request, error=None):
    return {
        "req": instrument_request,
        "items": RequestItem.objects.filter(request=instrument_request),
        "batches": SterilizationBatch.objects.all(),
        "error": error,
    }


@login_required
def mark_collected(request, request_id):
    if request.method != "POST":
        return HttpResponseForbidden("Method not allowed")
    instrument_request = get_object_or_404(InstrumentRequest, id=request_id)
    if instrument_request.status != "Requested":
        return render(
            request,
            "cssd-request-details.html",
            _detail_context(
                instrument_request,
                error=f"Cannot mark as Collected: request is currently '{instrument_request.status}'.",
            ),
        )
    instrument_request.status = "Collected"
    instrument_request.collected_at = timezone.now()
    instrument_request.last_operator = request.user
    instrument_request.save()
    Notification.objects.create(
        recipient=instrument_request.requester,
        request=instrument_request,
        message=f"REQ-{instrument_request.id:04d} has been collected by CSSD and is now being processed.",
    )
    return redirect("cssd_request_details", request_id=request_id)


@login_required
def mark_cleaned(request, request_id):
    if request.method != "POST":
        return HttpResponseForbidden("Method not allowed")
    instrument_request = get_object_or_404(InstrumentRequest, id=request_id)
    if instrument_request.status != "Collected":
        return render(
            request,
            "cssd-request-details.html",
            _detail_context(
                instrument_request,
                error=(
                    f"Cannot mark as Cleaned: request is currently '{instrument_request.status}'. "
                    "Only 'Collected' requests can be cleaned."
                ),
            ),
        )
    instrument_request.status = "Cleaned"
    instrument_request.cleaned_at = timezone.now()
    instrument_request.last_operator = request.user
    instrument_request.save()
    return redirect("cssd_request_details", request_id=request_id)


@login_required
def mark_sterilized(request, request_id):
    if request.method != "POST":
        return HttpResponseForbidden("Method not allowed")
    instrument_request = get_object_or_404(InstrumentRequest, id=request_id)
    if instrument_request.status != "Cleaned":
        return render(
            request,
            "cssd-request-details.html",
            _detail_context(
                instrument_request,
                error=(
                    f"Cannot mark as Sterilized: request is currently '{instrument_request.status}'. "
                    "Only 'Cleaned' requests can be sterilized."
                ),
            ),
        )
    batch_id = request.POST.get("batch_id")
    if batch_id:
        instrument_request.batch = get_object_or_404(SterilizationBatch, id=batch_id)
    instrument_request.status = "Sterilized"
    instrument_request.sterilized_at = timezone.now()
    instrument_request.last_operator = request.user
    instrument_request.save()
    return redirect("cssd_request_details", request_id=request_id)


@login_required
def mark_packed(request, request_id):
    if request.method != "POST":
        return HttpResponseForbidden("Method not allowed")
    instrument_request = get_object_or_404(InstrumentRequest, id=request_id)
    if instrument_request.status != "Sterilized":
        return render(
            request,
            "cssd-request-details.html",
            _detail_context(
                instrument_request,
                error=(
                    f"Cannot mark as Packed: request is currently '{instrument_request.status}'. "
                    "Only 'Sterilized' requests can be packed."
                ),
            ),
        )
    instrument_request.status = "Packed"
    instrument_request.packed_at = timezone.now()
    instrument_request.last_operator = request.user
    instrument_request.save()
    return redirect("cssd_request_details", request_id=request_id)


@login_required
def mark_delivered(request, request_id):
    if request.method != "POST":
        return HttpResponseForbidden("Method not allowed")

    instrument_request = get_object_or_404(InstrumentRequest, id=request_id)
    if request.user.department != instrument_request.department:
        return render(
            request,
            "nurse-request-details.html",
            {
                "req": instrument_request,
                "items": RequestItem.objects.filter(request=instrument_request),
                "eta": instrument_request.get_eta(),
                "error": (
                    f"Access Denied: Only nurses from the '{instrument_request.department}' "
                    "department can confirm delivery of this request."
                ),
            },
        )
    if instrument_request.status != "Packed":
        return render(
            request,
            "nurse-request-details.html",
            {
                "req": instrument_request,
                "items": RequestItem.objects.filter(request=instrument_request),
                "eta": instrument_request.get_eta(),
                "error": (
                    f"Cannot confirm delivery: request is currently '{instrument_request.status}'. "
                    "Only 'Packed' requests can be marked as Delivered."
                ),
            },
        )
    instrument_request.status = "Delivered"
    instrument_request.delivered_at = timezone.now()
    instrument_request.is_archived = True
    instrument_request.save()
    for item in RequestItem.objects.filter(request=instrument_request):
        item.inventory_item.current_stock += item.quantity
        item.inventory_item.save()
    return redirect("nurse_request_details", request_id=request_id)


@login_required
def cssd_request_details(request, request_id):
    instrument_request = get_object_or_404(InstrumentRequest, id=request_id)
    return render(
        request, "cssd-request-details.html", _detail_context(instrument_request)
    )


@login_required
def nurse_sterile_stock(request):
    packed_requests = InstrumentRequest.objects.filter(status="Packed").prefetch_related(
        "items__inventory_item"
    )
    return render(request, "nurse-sterile-stock.html", {"packed_requests": packed_requests})

# Create your views here.
