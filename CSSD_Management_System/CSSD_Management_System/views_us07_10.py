"""
=======================================================================
  views_us07_10.py — Instrument State Transition Views
  Author : Mohamed Badawy
  Sprint : 2
  User Stories implemented here:
      US-07  Mark Instrument as Collected   (Requested  → Collected)
      US-08  Mark Instrument as Cleaned     (Collected  → Cleaned)
      US-09  Mark Instrument as Sterilized  (Cleaned    → Sterilized)
      US-10  Mark Instrument as Packed      (Sterilized → Packed)

  Supporting views (also authored here):
      cssd_request_details  — Django-rendered CSSD detail page
      nurse_sterile_stock   — Nurse view of all Packed requests (US-10)

  Each transition:
    1. Verifies the pre-condition (correct current state)
    2. Records the exact UTC timestamp for that stage
    3. Sets last_operator to the acting CSSD Technician
    4. Creates a Notification for the requesting nurse (US-07 only per SRS)
    5. Redirects back to the request detail page on success, or
       re-renders the page with a clear error banner on failure.

  NOTE (temporary): Batch ID is optional for the Sterilized transition.
  The SRS requires it, but it is relaxed here for demo purposes.
=======================================================================
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.utils import timezone

from .models import (
    InstrumentRequest,
    RequestItem,
    SterilizationBatch,
    Notification,
)


# ─────────────────────────────────────────────────────────────────────────────
# Helper — build the common context dict for the CSSD detail page
# ─────────────────────────────────────────────────────────────────────────────
def _detail_context(instrument_request, error=None):
    return {
        'req':     instrument_request,
        'items':   RequestItem.objects.filter(request=instrument_request),
        'batches': SterilizationBatch.objects.all(),
        'error':   error,
    }


# ─────────────────────────────────────────────────────────────────────────────
# US-07  Mark as Collected   (Requested → Collected)
# ─────────────────────────────────────────────────────────────────────────────
@login_required
def mark_collected(request, request_id):
    """
    US-07 — Mark Instrument as Collected.

    Acceptance criteria:
    • Given an instrument request is in 'Requested' state, When a CSSD Tech
      clicks 'Mark as Collected', Then the state changes to 'Collected' and a
      timestamp is saved.
    • Given the state has changed to 'Collected', When the update is saved,
      Then the requesting Nurse receives a notification.
    """
    if request.method != 'POST':
        return HttpResponseForbidden("Method not allowed")

    instrument_request = get_object_or_404(InstrumentRequest, id=request_id)

    # Pre-condition check (AC 1)
    if instrument_request.status != 'Requested':
        return render(request, 'cssd-request-details.html',
                      _detail_context(instrument_request,
                                      error=f"Cannot mark as Collected: "
                                            f"request is currently '{instrument_request.status}'."))

    # State transition + timestamp (AC 1)
    instrument_request.status       = 'Collected'
    instrument_request.collected_at = timezone.now()
    instrument_request.last_operator = request.user
    instrument_request.save()

    # Nurse notification (AC 2)
    Notification.objects.create(
        recipient=instrument_request.requester,
        request=instrument_request,
        message=(f"REQ-{instrument_request.id:04d} has been collected by CSSD "
                 f"and is now being processed."),
    )

    return redirect('cssd_request_details', request_id=request_id)


# ─────────────────────────────────────────────────────────────────────────────
# US-08  Mark as Cleaned     (Collected → Cleaned)
# ─────────────────────────────────────────────────────────────────────────────
@login_required
def mark_cleaned(request, request_id):
    """
    US-08 — Mark Instrument as Cleaned.

    Acceptance criteria:
    • Given an instrument is in 'Collected' state, When a CSSD Tech clicks
      'Mark as Cleaned', Then the state changes to 'Cleaned' and a timestamp
      is recorded.
    • Given an instrument is NOT in 'Collected' state, When a CSSD Tech
      attempts to mark it as 'Cleaned', Then the system blocks the transition
      and displays an error.
    """
    if request.method != 'POST':
        return HttpResponseForbidden("Method not allowed")

    instrument_request = get_object_or_404(InstrumentRequest, id=request_id)

    # Pre-condition check (AC 2 — block invalid transition)
    if instrument_request.status != 'Collected':
        return render(request, 'cssd-request-details.html',
                      _detail_context(instrument_request,
                                      error=f"Cannot mark as Cleaned: "
                                            f"request is currently '{instrument_request.status}'. "
                                            f"Only 'Collected' requests can be cleaned."))

    # State transition + timestamp (AC 1)
    instrument_request.status       = 'Cleaned'
    instrument_request.cleaned_at   = timezone.now()
    instrument_request.last_operator = request.user
    instrument_request.save()

    return redirect('cssd_request_details', request_id=request_id)


# ─────────────────────────────────────────────────────────────────────────────
# US-09  Mark as Sterilized  (Cleaned → Sterilized)  [batch optional]
# ─────────────────────────────────────────────────────────────────────────────
@login_required
def mark_sterilized(request, request_id):
    """
    US-09 — Mark Instrument as Sterilized.

    Acceptance criteria:
    • Given an instrument is in 'Cleaned' state, When a CSSD Tech clicks
      'Mark as Sterilized', Then the state changes to 'Sterilized' and a
      timestamp is recorded.
    • Batch ID is optional (temporary relaxation for demo — SRS requires it).
    """
    if request.method != 'POST':
        return HttpResponseForbidden("Method not allowed")

    instrument_request = get_object_or_404(InstrumentRequest, id=request_id)

    # Pre-condition: must be in 'Cleaned' state
    if instrument_request.status != 'Cleaned':
        return render(request, 'cssd-request-details.html',
                      _detail_context(instrument_request,
                                      error=f"Cannot mark as Sterilized: "
                                            f"request is currently '{instrument_request.status}'. "
                                            f"Only 'Cleaned' requests can be sterilized."))

    # Batch is optional — link it only if one was chosen
    batch_id = request.POST.get('batch_id')
    if batch_id:
        batch = get_object_or_404(SterilizationBatch, id=batch_id)
        instrument_request.batch = batch

    # State transition + timestamp
    instrument_request.status        = 'Sterilized'
    instrument_request.sterilized_at = timezone.now()
    instrument_request.last_operator = request.user
    instrument_request.save()

    return redirect('cssd_request_details', request_id=request_id)


# ─────────────────────────────────────────────────────────────────────────────
# US-10  Mark as Packed      (Sterilized → Packed)
# ─────────────────────────────────────────────────────────────────────────────
@login_required
def mark_packed(request, request_id):
    """
    US-10 — Mark Instrument as Packed.

    Acceptance criteria:
    • Given an instrument is in 'Sterilized' state, When a CSSD Tech clicks
      'Mark as Packed', Then the state changes to 'Packed'.
    • Given an instrument state is now 'Packed', When a Nurse views the sterile
      stock list, Then the instrument appears as available in the list.
      (The sterile-stock list is served by nurse_sterile_stock below.)
    """
    if request.method != 'POST':
        return HttpResponseForbidden("Method not allowed")

    instrument_request = get_object_or_404(InstrumentRequest, id=request_id)

    # Pre-condition check
    if instrument_request.status != 'Sterilized':
        return render(request, 'cssd-request-details.html',
                      _detail_context(instrument_request,
                                      error=f"Cannot mark as Packed: "
                                            f"request is currently '{instrument_request.status}'. "
                                            f"Only 'Sterilized' requests can be packed."))

    # State transition + timestamp
    instrument_request.status        = 'Packed'
    instrument_request.packed_at     = timezone.now()
    instrument_request.last_operator = request.user
    instrument_request.save()

    return redirect('cssd_request_details', request_id=request_id)


# ─────────────────────────────────────────────────────────────────────────────
# CSSD Request Details page — Django-rendered (supports US-07 to US-10)
# ─────────────────────────────────────────────────────────────────────────────
@login_required
def cssd_request_details(request, request_id):
    """
    Renders the CSSD request-details page with live database data.
    The page exposes the correct action button for the current state,
    powering all four US-07–10 transitions.
    """
    instrument_request = get_object_or_404(InstrumentRequest, id=request_id)
    return render(request, 'cssd-request-details.html',
                  _detail_context(instrument_request))


# ─────────────────────────────────────────────────────────────────────────────
# Nurse Sterile Stock page — US-10 acceptance criterion (Packed → visible)
# ─────────────────────────────────────────────────────────────────────────────
@login_required
def nurse_sterile_stock(request):
    """
    US-10 — Nurse views the sterile stock list.
    All instrument requests in 'Packed' state appear here as available stock.
    """
    packed_requests = (
        InstrumentRequest.objects
        .filter(status='Packed')
        .prefetch_related('items__inventory_item')
    )
    return render(request, 'nurse-sterile-stock.html',
                  {'packed_requests': packed_requests})
