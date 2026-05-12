from datetime import datetime, timedelta

from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Q, Sum
from django.http import HttpResponse, HttpResponseForbidden, HttpResponseNotAllowed
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

from .decorators import cssd_staff_required, hospital_admin_required
from .forms import EmailLoginForm, SterilizationBatchForm
from .models import (CustomUser, InstrumentRequest, InstrumentSet, InventoryItem,
                     Notification, RequestItem, SterilizationBatch)

# US-29: View Estimated Completion Time (ETA)
# This branch isolates only the ETA display feature.
# Nurses can view the estimated time remaining for their instrument request
# to complete the sterilization pipeline based on its current status.

# US-27: View Inventory Shortage Alerts
# CSSD staff can view items whose current stock is at or below the minimum threshold.









def login_view(request):
    role_type = request.POST.get('portal_role') or request.GET.get('role')
    template_name = 'nurse-login.html' if role_type == 'nurse' else 'staff-login.html'
    if request.method == 'POST':
        form = EmailLoginForm(request, data=request.POST)
        
        if form.is_valid():
            user = form.get_user()
            staff_roles = {'CSSD Technician', 'System Administrator', 'Hospital Administrator'}
            if role_type == 'nurse' and user.role != 'Department Nurse':
                form.add_error(None, "This account is not allowed to use this portal.")
                return render(request, template_name, {'form': form})
            if role_type == 'staff' and user.role not in staff_roles:
                form.add_error(None, "This account is not allowed to use this portal.")
                return render(request, template_name, {'form': form})
            login(request, user)
            if user.role == 'Department Nurse':
                return redirect('nurse_dashboard')
            return redirect('cssd_dashboard')
    else:
        form = EmailLoginForm()
    return render(request, template_name, {'form': form})


def home(request):
    if request.user.is_authenticated:
        return redirect('dashboard_router')
    return render(request, 'index.html')


def logout_view(request):
    logout(request)
    return redirect('home')


@login_required
def dashboard_router(request):
    """
    FR-02: Role-Based Dashboard Routing
    Detects the user's role and routes them to their corresponding dashboard.
    """
    role = request.user.role

    if role in ['CSSD Technician', 'System Administrator', 'Hospital Administrator']:
        filter_status = request.GET.get('filter', '')

        all_requests = InstrumentRequest.objects.prefetch_related(
            'items__inventory_item', 'requester'
        ).order_by('-submitted_at')

        display_requests = (
            all_requests.filter(status='Requested')
            if filter_status == 'pending'
            else all_requests
        )

        stat_pending = all_requests.filter(status='Requested').count()
        stat_active  = all_requests.filter(
            status__in=['Collected', 'Cleaned', 'Sterilized', 'Packed']
        ).count()
        stat_alerts  = InventoryItem.objects.filter(current_stock__lt=3).count()
        STATUS_ORDER = ['Requested', 'Collected', 'Cleaned', 'Sterilized', 'Packed', 'Delivered']
        urgent_reqs  = all_requests.filter(priority='Urgent').exclude(status='Delivered')
        eta_text, eta_desc = 'No urgent', 'All clear'
        if urgent_reqs.exists():
            def eta_mins(r):
                idx = STATUS_ORDER.index(r.status) if r.status in STATUS_ORDER else 0
                return max(0, (len(STATUS_ORDER) - 1 - idx) * 20)
            mins = min(eta_mins(r) for r in urgent_reqs)
            eta_text = f'~{mins} min' if mins < 60 else f'~{mins // 60:.1f} hr'
            eta_desc = f'{urgent_reqs.count()} urgent request(s) pending'

        context = {
            'requests':      display_requests,
            'filter_status': filter_status,
            'stat_pending':  stat_pending,
            'stat_active':   stat_active,
            'stat_alerts':   stat_alerts,
            'eta_text':      eta_text,
            'eta_desc':      eta_desc,
        }
        return render(request, 'cssd-dashboard.html', context)

    elif role == 'Department Nurse':
        return nurse_dashboard(request)
    return HttpResponse(f"Role '{role}' not recognized.", status=403)



@login_required
def nurse_dashboard(request):
    final_requests = []

    requests = InstrumentRequest.objects.filter(requester=request.user)

    
    for request_obj in requests:
        request_dict = {
            'id': request_obj.id,
            'instruments': RequestItem.objects.filter(request=request_obj),
            'priority': request_obj.priority,
            'status': request_obj.status,
            'department': request_obj.department,
            'notes': request_obj.notes,
            'created_at': request_obj.submitted_at,
        }
        final_requests.append(request_dict)

    unread_notifications = Notification.objects.filter(
        recipient=request.user, is_read=False
    ).order_by('-created_at')

    context = {
        'requests': final_requests,
        'total': len(requests),
        'in_progress': len(requests.filter(status__in=['Collected', 'Cleaned', 'Sterilized', 'Packed'])),
        'urgent': len(requests.filter(priority='Urgent')),
        'delivered': len(requests.filter(status='Delivered')),
        'notifications': unread_notifications,
        'notif_count': unread_notifications.count(),
    }

    return render(request, 'nurse-dashboard.html', context)



@login_required
def nurse_mark_notifications_read(request):
    """Mark all unread notifications for the current nurse as read."""
    if request.method == 'POST':
        Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
    return redirect('nurse_dashboard')



def get_instruments():
    instruments = []
    for instrument in InventoryItem.objects.all():
        instruments.append({
            'name': instrument.name,
            'category': instrument.category,
            'current_stock': instrument.current_stock,
            'min_threshold': instrument.min_threshold,
        })
    return instruments



@login_required
def nurse_create_request(request):
    if request.method == 'POST':
        return save_instrument_request(request)
    return render(request, 'nurse-create-request.html', {'instruments': get_instruments()})


@csrf_exempt
@login_required
def save_instrument_request(request):
    if request.user.role != 'Department Nurse':
        return HttpResponseForbidden("Only department nurses can submit instrument requests.")

    if request.method == 'POST':
        instruments = request.POST.getlist('instruments')
        priority = request.POST.get('priority')
        notes = request.POST.get('notes') or ''

        requested_items = []
        selected_instruments = []
        if instruments:
            for instrument in instruments:
                selected_instruments.append((
                    instrument,
                    InventoryItem.objects.get(name=instrument),
                    request.POST.get("quantity_" + instrument, "0"),
                ))
        else:
            for key, value in request.POST.items():
                if not key.startswith("quantity_"):
                    continue
                item_id = key.removeprefix("quantity_")
                if not item_id.isdigit():
                    continue
                try:
                    database_instrument = InventoryItem.objects.get(pk=int(item_id))
                except InventoryItem.DoesNotExist:
                    continue
                selected_instruments.append((database_instrument.name, database_instrument, value))

        if not selected_instruments:
            messages.warning(request, "Select at least one instrument.")
            return redirect('nurse_create_request')

        for instrument, database_instrument, raw_quantity in selected_instruments:
            try:
                quantity = int(raw_quantity)
            except (TypeError, ValueError):
                quantity = 0

            if quantity <= 0:
                messages.warning(request, "Select at least one instrument with a quantity greater than zero.")
                return redirect('nurse_create_request')

            if quantity > database_instrument.current_stock:
                messages.warning(
                    request,
                    f"Insufficient stock for {instrument}. Available: {database_instrument.current_stock}.",
                )
                return redirect('nurse_create_request')

            requested_items.append((database_instrument, quantity))

        with transaction.atomic():
            new_request = InstrumentRequest.objects.create(
                requester=request.user,
                priority=priority,
                department=request.user.department,
                notes=notes,
            )

            for database_instrument, quantity in requested_items:
                RequestItem.objects.create(
                    request=new_request,
                    inventory_item=database_instrument,
                    quantity=quantity,
                )
                database_instrument.current_stock -= quantity
                database_instrument.save()

        messages.success(request, f"Request REQ-{new_request.id:04d} sent successfully.")
        return redirect('nurse_dashboard')
    return redirect('nurse_create_request')


def _notify_nurse(request_obj, message):
    Notification.objects.create(
        recipient=request_obj.requester,
        request=request_obj,
        message=message,
    )


@login_required
@cssd_staff_required
def cssd_dashboard(request):
    all_requests = InstrumentRequest.objects.filter(is_archived=False).order_by('-submitted_at')
    context = {
        'staff_name': request.user.email.split('@')[0].capitalize(),
        'staff_role': request.user.role,
        'stats': {
            'pending': all_requests.filter(status='Requested').count(),
            'in_progress': all_requests.filter(status__in=['Collected', 'Cleaned', 'Sterilized', 'Packed']).count(),
            'completed': all_requests.filter(status='Delivered').count(),
            'alerts': InventoryItem.objects.filter(current_stock__lt=3).count(),
        },
        'requests': all_requests[:10],
        'show_pending_only': False,
    }
    return render(request, 'cssd-dashboard.html', context)


@login_required
@cssd_staff_required
def cssd_request_detail(request, pk):
    req = get_object_or_404(InstrumentRequest, pk=pk)
    return render(request, 'cssd-request-details.html', {'req': req, 'batches': []})


@login_required
@cssd_staff_required
def cssd_update_request_status(request, pk, status):
    """
    Unified transition view for Proj-17 (Collected), Proj-18 (Cleaned), Proj-19 (Sterilized).
    Only POST requests are accepted; GET returns 405.
    """
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])

    req = get_object_or_404(InstrumentRequest, pk=pk)

    valid_transitions = {
        'Collected': 'Requested',
        'Cleaned': 'Collected',
        'Sterilized': 'Cleaned',
        'Packed': 'Sterilized',
        'Delivered': 'Packed',
    }

    if status not in valid_transitions:
        messages.error(request, f"Invalid transition status: '{status}'.")
        return redirect('cssd_request_detail', pk=pk)

    if req.status == 'Collected' and status != 'Cleaned':
        messages.error(request, "Can only mark as Cleaned from Collected.")
        return redirect('cssd_request_detail', pk=pk)

    if req.status != valid_transitions[status]:
        messages.error(request, f"Can only mark as {status} from {valid_transitions[status]}. Current status: '{req.status}'.")
        return redirect('cssd_request_detail', pk=pk)

    if status == 'Sterilized':
        batch_id = request.POST.get('batch_id') or request.GET.get('batch_id')
        if not batch_id:
            messages.error(request, 'A sterilization batch ID is required before marking as Sterilized.')
            return redirect('cssd_request_detail', pk=pk)
        try:
            req.batch = SterilizationBatch.objects.get(pk=batch_id)
        except SterilizationBatch.DoesNotExist:
            messages.error(request, 'Batch not found.')
            return redirect('cssd_request_detail', pk=pk)
        req.sterilized_at = timezone.now()
    elif status == 'Collected':
        req.collected_at = timezone.now()
    elif status == 'Cleaned':
        req.cleaned_at = timezone.now()
    elif status == 'Packed':
        req.packed_at = timezone.now()
    elif status == 'Delivered':
        req.delivered_at = timezone.now()

    req.status = status
    req.last_operator = request.user
    req.save()
    
    _notify_nurse(req, f'REQ-{req.id:04d} instruments have been {status.lower()}.')
    messages.success(request, f'REQ-{req.id:04d} marked as {status}.')
    return redirect('cssd_request_detail', pk=pk)


# ---------------------------------------------------------------------------
# US-24: Assign Operator to Batch  ← FEATURE
# ---------------------------------------------------------------------------

@login_required
@cssd_staff_required
def cssd_batch_list(request):
    """
    US-24: Lists all sterilization batches, showing assigned operator per batch.
    """
    batches = SterilizationBatch.objects.all().order_by('-created_at')
    return render(request, 'cssd-batch-list.html', {'batches': batches})


@login_required
@cssd_staff_required
def cssd_batch_create(request):
    """Supporting view: create a sterilization batch to use with this feature."""
    """
    US-24: Creates a new sterilization batch and assigns the current user as operator.
    The logged-in CSSD technician is automatically set as the batch operator.
    """
    if request.method == 'POST':
        form = SterilizationBatchForm(request.POST)
        if form.is_valid():
            batch = form.save(commit=False)
            batch.operator = request.user
            batch.save()
            messages.success(request, f'Batch #{batch.id} created.')
            return redirect('cssd_dashboard')
    else:
        form = SterilizationBatchForm()
    return render(request, 'cssd-batch-create.html', {'form': form})


@login_required
@hospital_admin_required
def hospital_report(request):
    date_str = request.GET.get('date', timezone.localdate().isoformat())
    try:
        report_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        report_date = timezone.localdate()
        date_str = report_date.isoformat()

    nurse_requests = InstrumentRequest.objects.filter(
        submitted_at__date=report_date,
    ).select_related('requester').prefetch_related(
        'items__inventory_item'
    ).order_by('-submitted_at')

    technician_filters = (
        Q(collected_at__date=report_date)
        | Q(cleaned_at__date=report_date)
        | Q(sterilized_at__date=report_date)
        | Q(packed_at__date=report_date)
        | Q(delivered_at__date=report_date)
    )
    processed_requests = InstrumentRequest.objects.filter(
        technician_filters
    ).select_related('requester', 'batch', 'batch__operator', 'last_operator').prefetch_related(
        'items__inventory_item'
    ).distinct()

    def happened_on_report_day(value):
        return value and timezone.localtime(value).date() == report_date

    technician_actions = []
    for req in processed_requests:
        action_rows = [
            ('Collected', req.collected_at),
            ('Cleaned', req.cleaned_at),
            ('Sterilized', req.sterilized_at),
            ('Packed', req.packed_at),
            ('Delivered', req.delivered_at),
        ]
        for action, happened_at in action_rows:
            if happened_on_report_day(happened_at):
                technician_actions.append({
                    'request': req,
                    'action': action,
                    'happened_at': happened_at,
                    'operator': req.last_operator or (req.batch.operator if req.batch else None),
                })
    technician_actions.sort(key=lambda row: row['happened_at'], reverse=True)

    requests = InstrumentRequest.objects.filter(
        sterilized_at__date=report_date,
    ).select_related('requester', 'batch', 'batch__operator', 'last_operator').prefetch_related(
        'items__inventory_item'
    )

    batches = SterilizationBatch.objects.filter(
        Q(created_at__date=report_date) | Q(requests__sterilized_at__date=report_date),
    ).distinct()

    operators = CustomUser.objects.filter(
        Q(processed_requests__collected_at__date=report_date)
        | Q(processed_requests__cleaned_at__date=report_date)
        | Q(processed_requests__sterilized_at__date=report_date)
        | Q(processed_requests__packed_at__date=report_date)
        | Q(processed_requests__delivered_at__date=report_date),
        role='CSSD Technician',
    ).distinct()

    total_items = (
        RequestItem.objects
        .filter(request__in=requests)
        .aggregate(total=Sum('quantity'))['total']
        or 0
    )

    context = {
        'date_str': date_str,
        'report_date': report_date.strftime('%d %b %Y'),
        'nurse_requests': nurse_requests,
        'technician_actions': technician_actions,
        'requests': requests,
        'batches': batches,
        'total_batches': batches.count(),
        'total_sterilized': total_items,
        'total_requests': requests.count(),
        'total_submitted': nurse_requests.count(),
        'total_tech_actions': len(technician_actions),
        'operators': operators,
    }
    return render(request, 'hospital-report.html', context)


@login_required
@hospital_admin_required
def hospital_audit(request):
    query = request.GET.get('q', '').strip()
    results = InstrumentRequest.objects.none()

    if query:
        filters = Q(items__inventory_item__name__icontains=query)
        if query.upper().startswith('REQ-'):
            query_id = query[4:]
        else:
            query_id = query
        if query_id.isdigit():
            filters |= Q(id=int(query_id))

        results = (
            InstrumentRequest.objects
            .filter(filters)
            .select_related('requester', 'batch', 'batch__operator')
            .prefetch_related('items__inventory_item')
            .distinct()
            .order_by('-submitted_at')
        )

    return render(request, 'hospital-audit.html', {
        'query': query,
        'results': results,
    })


@login_required
def mark_delivered(request, request_id):
    if request.method != 'POST':
        return HttpResponseForbidden("Method not allowed")

    instrument_request = get_object_or_404(InstrumentRequest, id=request_id)

    def _nurse_error_context(error):
        return {
            'req':   instrument_request,
            'items': RequestItem.objects.filter(request=instrument_request),
            'eta':   instrument_request.get_eta(),
            'error': error,
        }

    if request.user.role != 'Department Nurse':
        return HttpResponseForbidden("Only department nurses can confirm delivery.")

    if request.user.department != instrument_request.department:
        return render(
            request,
            'nurse-request-details.html',
            _nurse_error_context(
                f"Access Denied: Only nurses from the "
                f"'{instrument_request.department}' department "
                f"can confirm delivery of this request."
            ),
        )

    if instrument_request.status != 'Packed':
        return render(
            request,
            'nurse-request-details.html',
            _nurse_error_context(
                f"Cannot confirm delivery: request is currently "
                f"'{instrument_request.status}'. "
                f"Only 'Packed' requests can be marked as Delivered."
            ),
        )

    instrument_request.status = 'Delivered'
    instrument_request.delivered_at = timezone.now()
    instrument_request.is_archived = True
    instrument_request.save()

    for item in RequestItem.objects.filter(request=instrument_request):
        item.inventory_item.current_stock += item.quantity
        item.inventory_item.save()

    return redirect('nurse_request_details', request_id=request_id)


@login_required
def nurse_request_detail_compat(request, pk):
    if request.method == 'POST' and request.POST.get('action') == 'deliver':
        return mark_delivered(request, pk)
    return nurse_request_details(request, pk)


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
@cssd_staff_required
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
@cssd_staff_required
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
@cssd_staff_required
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
@cssd_staff_required
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
@cssd_staff_required
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
@login_required
@cssd_staff_required
def cssd_batch_detail(request, pk):
    """
    US-24: Shows batch details including operator name and linked requests.
    """
    batch = get_object_or_404(SterilizationBatch, pk=pk)
    linked_requests = InstrumentRequest.objects.filter(batch=batch)
    return render(request, 'cssd-batch-detail.html', {
        'batch': batch,
        'linked_requests': linked_requests,
})


# ---------------------------------------------------------------------------
# US-29: View Estimated Completion Time  ← FEATURE
# ---------------------------------------------------------------------------

# Average minutes remaining per status stage
_ETA_MINUTES = {
    'Requested':  120,   # ~2 hours: collection + cleaning + sterilization + packing
    'Collected':   90,   # ~1.5 hours: cleaning + sterilization + packing
    'Cleaned':     60,   # ~1 hour: sterilization + packing
    'Sterilized':  30,   # ~30 min: packing + delivery
    'Packed':      15,   # ~15 min: final delivery
    'Delivered':    0,
}


def _compute_eta(req):
    """
    Calculates ETA string for a given InstrumentRequest based on its current status.
    Uses the last known timestamp for the current stage as the calculation base.
    """
    if req.status == 'Delivered':
        return 'Ready'

    remaining_minutes = _ETA_MINUTES.get(req.status, 0)

    # Use the most recent stage timestamp as the base, fall back to submitted_at
    base_time = (
        req.packed_at or req.sterilized_at or
        req.cleaned_at or req.collected_at or
        req.submitted_at or timezone.now()
    )

    eta_time = base_time + timedelta(minutes=remaining_minutes)
    now = timezone.now()

    if eta_time <= now:
        return 'Overdue — awaiting processing'

    delta = eta_time - now
    total_minutes = int(delta.total_seconds() // 60)
    hours, mins = divmod(total_minutes, 60)

    if hours > 0:
        time_str = f'{hours}h {mins}m'
    else:
        time_str = f'{mins}m'

    return f'~{time_str} (Ready by {eta_time.strftime("%I:%M %p")})'


@login_required
def nurse_request_details(request, request_id):
    """
    US-29: Displays detailed request info including the Estimated Completion Time.
    The ETA is computed live based on current status and last-updated timestamp.
    """
    
    pk = request_id
    req = get_object_or_404(InstrumentRequest, pk=pk)


    if request.user != req.requester:
        return HttpResponseForbidden("You can only view your own requests")
    
    # Only show ETA for requests belonging to this nurse
    if req.requester != request.user:
        messages.error(request, 'You can only view your own requests.')
        return redirect('nurse_dashboard')

    eta = _compute_eta(req)
    eta_breakdown = {
        status: mins
        for status, mins in _ETA_MINUTES.items()
        if mins > 0
    }

    return render(request, 'nurse-request-details.html', {
        'req': req,
        'eta': eta,
        'eta_breakdown': eta_breakdown,
        'remaining_minutes': _ETA_MINUTES.get(req.status, 0),
    })
# ---------------------------------------------------------------------------
# US-27: View Inventory Shortage Alerts  ← FEATURE
# ---------------------------------------------------------------------------

@login_required
@cssd_staff_required
def cssd_inventory_alerts(request):
    """
    US-27: Displays all inventory items whose current_stock is at or below
    their min_threshold, alerting CSSD staff to restock before shortages occur.
    Items are categorised as:
      - 'Out of Stock'  : current_stock == 0
      - 'Critical'      : 0 < current_stock <= min_threshold
    """
    category_filter = request.GET.get('category', '')

    from django.db.models import F
    shortage_items = InventoryItem.objects.filter(
        current_stock__lte=F('min_threshold')
    ).order_by('current_stock', 'name')

    if category_filter:
        shortage_items = shortage_items.filter(category=category_filter)

    categories = InventoryItem.objects.values_list('category', flat=True).distinct()

    # Annotate severity label
    alert_data = []
    for item in shortage_items:
        if item.current_stock == 0:
            severity = 'Out of Stock'
        else:
            severity = 'Critical'
        alert_data.append({'item': item, 'severity': severity})

    out_of_stock_count = sum(1 for entry in alert_data if entry['severity'] == 'Out of Stock')
    critical_count = sum(1 for entry in alert_data if entry['severity'] == 'Critical')

    return render(request, 'cssd-inventory-alerts.html', {
        'alert_data': alert_data,
        'shortage_count': shortage_items.count(),
        'out_of_stock_count': out_of_stock_count,
        'critical_count': critical_count,
        'categories': categories,
        'selected_category': category_filter,
    })
