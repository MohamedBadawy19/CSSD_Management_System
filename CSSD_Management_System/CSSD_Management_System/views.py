from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from .forms import EmailLoginForm, SterilizationBatchForm
from django.http import HttpResponse, HttpResponseForbidden, HttpResponseNotAllowed
from django.views.decorators.csrf import csrf_exempt
from .models import InstrumentSet, RequestItem, InstrumentRequest, InventoryItem, Notification, SterilizationBatch
from .decorators import cssd_staff_required
from django.contrib import messages
from django.utils import timezone


@csrf_exempt
def login_view(request):
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
    role = request.user.role

    if role in ['CSSD Technician', 'System Administrator', 'Hospital Administrator']:
        return render(request, 'cssd-dashboard.html')
    if role == 'Department Nurse':
        return render(request, 'nurse-dashboard.html')
    return HttpResponse(f"Role '{role}' not found. Please contact admin.", status=403)


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
        }
        final_requests.append(request_dict)

    context = {
        'requests': final_requests,
        'total': len(requests),
        'in_progress': len(requests.filter(status__in=['Collected', 'Cleaned', 'Sterilized', 'Packed'])),
        'urgent': len(requests.filter(priority='Urgent')),
        'delivered': len(requests.filter(priority='Delivered')),
    }

    return render(request, 'nurse-dashboard.html', context)


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
    return render(request, 'nurse-create-request.html', {'instruments': get_instruments()})


@csrf_exempt
def save_instrument_request(request):
    if request.method == 'POST':
        instruments = request.POST.getlist('instruments')
        priority = request.POST.get('priority')
        notes = request.POST.get('notes')

        new_request = InstrumentRequest.objects.create(
            requester=request.user,
            priority=priority,
            department=request.user.department,
            notes=notes,
        )

        for instrument in instruments:
            quantity = int(request.POST.get("quantity_" + instrument))
            database_instrument = InventoryItem.objects.get(name=instrument)

            if quantity > database_instrument.current_stock:
                return render(
                    request,
                    'nurse-create-request.html',
                    {
                        'instruments': get_instruments(),
                        'warning': f'instrument {instrument} has current_stock : {database_instrument.current_stock}',
                    },
                )

            RequestItem.objects.create(
                request=new_request,
                inventory_item=database_instrument,
                quantity=quantity,
            )
            database_instrument.current_stock -= quantity
            database_instrument.save()
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
    }

    if status not in valid_transitions:
        messages.error(request, f"Invalid transition status: '{status}'.")
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

    req.status = status
    req.last_operator = request.user
    req.save()
    
    _notify_nurse(req, f'REQ-{req.id:04d} instruments have been {status.lower()}.')
    messages.success(request, f'REQ-{req.id:04d} marked as {status}.')
    return redirect('cssd_request_detail', pk=pk)


@login_required
@cssd_staff_required
def cssd_batch_create(request):
    """Supporting view: create a sterilization batch to use with this feature."""
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


def nurse_request_details(request, request_id):
    instrument_request = InstrumentRequest.objects.get(id=request_id)
    if request.user == instrument_request.requester:
        status = ['Requested', 'Collected', 'Cleaned', 'Sterilized', 'Packed', 'Delivered']
        request_dict = {
            'req': instrument_request,
            'status_order': status,
            'current_status_index': status.index(instrument_request.status),
            'items': RequestItem.objects.filter(request=instrument_request),
        }
        return render(request, 'nurse-request-details.html', request_dict)

    return HttpResponseForbidden("Access Denined")
