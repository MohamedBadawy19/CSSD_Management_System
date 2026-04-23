from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from .forms import EmailLoginForm
from django.http import HttpResponse, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from .models import (
    InstrumentSet, RequestItem, InstrumentRequest,
    InventoryItem, Notification, SterilizationBatch
)
import datetime


@csrf_exempt
def login_view(request):
    # Determine which template to show based on a URL parameter
    role_type = request.GET.get('role', 'staff')
    template_name = 'nurse-login.html' if role_type == 'nurse' else 'staff-login.html'

    if request.method == 'POST':
        form = EmailLoginForm(request, data=request.POST)
        print(form.is_valid())
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('dashboard_router')
    else:
        form = EmailLoginForm()

    return render(request, template_name, {'form': form})


def home(request):
    if request.user.is_authenticated:
        return redirect('dashboard_router')
    return render(request, 'index.html')


def logout_view(request):
    logout(request)
    return redirect('login')


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
        return redirect('nurse_dashboard')
    else:
        return HttpResponse(f"Role '{role}' not found. Please contact admin.", status=403)


@login_required
def nurse_dashboard(request):
    final_requests = []
    requests = InstrumentRequest.objects.filter(requester=request.user)

    for req in requests:
        instruments = RequestItem.objects.filter(request=req)
        request_dict = {
            'id':         req.id,
            'instruments': instruments,
            'priority':   req.priority,
            'status':     req.status,
            'department': req.department,
            'notes':      req.notes,
        }
        final_requests.append(request_dict)

    total       = len(requests)
    in_progress = len(requests.filter(status__in=['Collected', 'Cleaned', 'Sterilized', 'Packed']))
    urgent      = len(requests.filter(priority='Urgent'))
    delivered   = len(requests.filter(status='Delivered'))

    context = {
        'requests':    final_requests,
        'total':       total,
        'in_progress': in_progress,
        'urgent':      urgent,
        'delivered':   delivered,
    }
    return render(request, 'nurse-dashboard.html', context)


def get_instruments():
    instruments = []
    for instrument in InventoryItem.objects.all():
        instrument_dict = {
            'name':          instrument.name,
            'category':      instrument.category,
            'current_stock': instrument.current_stock,
            'min_threshold': instrument.min_threshold,
        }
        instruments.append(instrument_dict)
    return instruments


@login_required
def nurse_create_request(request):
    return render(request, 'nurse-create-request.html', {'instruments': get_instruments()})


@csrf_exempt
def save_instrument_request(request):
    if request.method == 'POST':
        instruments = request.POST.getlist('instruments')
        priority    = request.POST.get('priority')
        notes       = request.POST.get('notes')

        new_request = InstrumentRequest.objects.create(
            requester=request.user,
            priority=priority,
            department=request.user.department,
            notes=notes,
            submitted_at=datetime.datetime.now(),
        )

        for instrument in instruments:
            quantity            = int(request.POST.get("quantity_" + instrument))
            database_instrument = InventoryItem.objects.get(name=instrument)

            if quantity > database_instrument.current_stock:
                return render(request, 'nurse-create-request.html', {
                    'instruments': get_instruments(),
                    'warning': f'instrument {instrument} has current_stock : {database_instrument.current_stock}',
                })

            RequestItem.objects.create(
                request=new_request,
                inventory_item=database_instrument,
                quantity=quantity,
            )
            database_instrument.current_stock -= quantity
            database_instrument.save()

    return redirect('nurse_create_request')


def nurse_request_details(request, request_id):
    instrument_request = InstrumentRequest.objects.get(id=request_id)
    if request.user == instrument_request.requester:
        request_dict = {
            'req':   instrument_request,
            'items': RequestItem.objects.filter(request=instrument_request),
            'eta':   instrument_request.get_eta(),
            'error' : None
        }
        return render(request, 'nurse-request-details.html', request_dict)

    return HttpResponseForbidden("Access Denied")


@login_required
def mark_delivered(request, request_id):
    """
    US-11 — Nurse confirms delivery of packed instruments.
 
    Acceptance criteria:
    • AC1: Given an instrument is in 'Packed' state, When ANY nurse from the
      requesting department marks it as 'Delivered', Then the state changes to
      'Delivered' and the record is archived (is_archived=True).
    • AC2: Given a nurse from a DIFFERENT department attempts to mark it as
      'Delivered', Then the system blocks the action and shows an error.
    """
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
 
   
    if request.user.department != instrument_request.department:
        return render(request, 'nurse-request-details.html',
                      _nurse_error_context(
                          f"Access Denied: Only nurses from the "
                          f"'{instrument_request.department}' department "
                          f"can confirm delivery of this request."
                      ))
 
    
    if instrument_request.status != 'Packed':
        return render(request, 'nurse-request-details.html',
                      _nurse_error_context(
                          f"Cannot confirm delivery: request is currently "
                          f"'{instrument_request.status}'. "
                          f"Only 'Packed' requests can be marked as Delivered."
                      ))
 
    # AC1 — state transition + timestamp + archive
    instrument_request.status       = 'Delivered'
    instrument_request.delivered_at = timezone.now()
    instrument_request.is_archived  = True
    instrument_request.save()
 
    return redirect('nurse_request_details', request_id=request_id)