import datetime

from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt

from .models import InventoryItem, InstrumentRequest, RequestItem


def get_instruments():
    return [
        {
            "name": instrument.name,
            "category": instrument.category,
            "current_stock": instrument.current_stock,
            "min_threshold": instrument.min_threshold,
        }
        for instrument in InventoryItem.objects.all()
    ]


@login_required
def nurse_create_request(request):
    return render(request, "nurse-create-request.html", {"instruments": get_instruments()})


@csrf_exempt
def save_instrument_request(request):
    if request.method != "POST":
        return redirect("nurse_create_request")

    instruments = request.POST.getlist("instruments")
    priority = request.POST.get("priority")
    notes = request.POST.get("notes")

    new_request = InstrumentRequest.objects.create(
        requester=request.user,
        priority=priority,
        department=request.user.department,
        notes=notes,
        submitted_at=datetime.datetime.now(),
    )

    for instrument in instruments:
        quantity = int(request.POST.get(f"quantity_{instrument}"))
        database_instrument = InventoryItem.objects.get(name=instrument)

        if quantity > database_instrument.current_stock:
            return render(
                request,
                "nurse-create-request.html",
                {
                    "instruments": get_instruments(),
                    "warning": (
                        f"instrument {instrument} has current_stock : "
                        f"{database_instrument.current_stock}"
                    ),
                },
            )

        RequestItem.objects.create(
            request=new_request, inventory_item=database_instrument, quantity=quantity
        )
        database_instrument.current_stock -= quantity
        database_instrument.save()

    return redirect("nurse_create_request")


@login_required
def nurse_request_details(request, request_id):
    instrument_request = InstrumentRequest.objects.get(id=request_id)
    if request.user != instrument_request.requester:
        return HttpResponseForbidden("Access Denied")

    return render(
        request,
        "nurse-request-details.html",
        {
            "req": instrument_request,
            "items": RequestItem.objects.filter(request=instrument_request),
            "eta": instrument_request.get_eta(),
            "error": None,
        },
    )

# Create your views here.
