# US-19: Mark Instrument Request as Sterilized
# This branch isolates only the "Mark as Sterilized" state transition.
# Requires linking a SterilizationBatch before the transition is allowed.

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from django.utils import timezone

from .forms import EmailLoginForm, SterilizationBatchForm, InventoryItemForm
from .decorators import cssd_staff_required
from .models import InstrumentRequest, RequestItem, InventoryItem, SterilizationBatch, Notification


def _notify_nurse(request_obj, message):
    Notification.objects.create(recipient=request_obj.requester, request=request_obj, message=message)


def login_view(request):
    role_type = request.GET.get('role', 'staff')
    template_name = 'nurse-login.html' if role_type == 'nurse' else 'staff-login.html'
    if request.method == 'POST':
        form = EmailLoginForm(request, data=request.POST)
        if form.is_valid():
            login(request, form.get_user())
            return redirect('dashboard_router')
    else:
        form = EmailLoginForm()
    return render(request, template_name, {'form': form})


def home(request):
    return render(request, 'index.html')


def logout_view(request):
    logout(request)
    return redirect('login')


@login_required
def dashboard_router(request):
    role = request.user.role
    if role in ['CSSD Technician', 'System Administrator', 'Hospital Administrator']:
        return redirect('cssd_dashboard')
    elif role == 'Department Nurse':
        return redirect('nurse_dashboard')
    return HttpResponse(f"Role '{role}' not recognized.", status=403)


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
    batches = SterilizationBatch.objects.all().order_by('-created_at')
    return render(request, 'cssd-request-details.html', {'req': req, 'batches': batches})


# ---------------------------------------------------------------------------
# US-19: Mark as Sterilized  ← FEATURE
# ---------------------------------------------------------------------------

@login_required
@cssd_staff_required
def cssd_update_request_status(request, pk, status):
    """
    US-19: Allows a CSSD technician to mark a Cleaned InstrumentRequest as Sterilized.
    Requires a valid SterilizationBatch to be linked before transition.
    Only the Cleaned → Sterilized transition is permitted in this branch.
    """
    req = get_object_or_404(InstrumentRequest, pk=pk)

    if status != 'Sterilized':
        messages.error(request, f"This branch only supports marking as Sterilized. Got: '{status}'.")
        return redirect('cssd_request_detail', pk=pk)

    if req.status != 'Cleaned':
        messages.error(request, f"Can only sterilize a Cleaned item. Current status: '{req.status}'.")
        return redirect('cssd_request_detail', pk=pk)

    batch_id = request.POST.get('batch_id') or request.GET.get('batch_id')
    if not batch_id:
        messages.error(request, 'A sterilization batch ID is required before marking as Sterilized.')
        return redirect('cssd_request_detail', pk=pk)
    try:
        req.batch = SterilizationBatch.objects.get(pk=batch_id)
    except SterilizationBatch.DoesNotExist:
        messages.error(request, 'Batch not found.')
        return redirect('cssd_request_detail', pk=pk)

    req.status = 'Sterilized'
    req.sterilized_at = timezone.now()
    req.last_operator = request.user
    req.save()
    _notify_nurse(req, f'REQ-{req.id:04d} instruments have been sterilized.')
    messages.success(request, f'REQ-{req.id:04d} marked as Sterilized.')
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


@login_required
def nurse_dashboard(request):
    all_requests = InstrumentRequest.objects.filter(requester=request.user).order_by('-submitted_at')
    unread = Notification.objects.filter(recipient=request.user, is_read=False).order_by('-created_at')
    context = {
        'nurse_name': request.user.email.split('@')[0].capitalize(),
        'nurse_ward': getattr(request.user, 'department', 'General Ward'),
        'stats': {
            'total': all_requests.count(),
            'in_progress': all_requests.filter(status__in=['Collected', 'Cleaned', 'Sterilized', 'Packed']).count(),
            'urgent': all_requests.filter(priority='Urgent').count(),
            'delivered': all_requests.filter(status='Delivered').count(),
        },
        'requests': all_requests.exclude(status='Delivered'),
        'notifications': unread,
        'notif_count': unread.count(),
    }
    return render(request, 'nurse-dashboard.html', context)


@login_required
def nurse_create_request(request):
    instruments = InventoryItem.objects.all().order_by('category', 'name')
    if request.method == 'POST':
        priority = request.POST.get('priority', 'Normal')
        notes = request.POST.get('notes', '')
        valid_items, has_error = [], False
        for item in instruments:
            qty_val = request.POST.get(f'quantity_{item.id}')
            if qty_val and qty_val.isdigit():
                qty = int(qty_val)
                if qty > 0:
                    if qty > item.current_stock:
                        messages.error(request, f"Insufficient stock for {item.name}.")
                        has_error = True
                    else:
                        valid_items.append((item, qty))
        if not valid_items and not has_error:
            messages.warning(request, "Select at least one instrument.")
            has_error = True
        if has_error:
            return render(request, 'nurse-create-request.html', {
                'instruments': instruments, 'priority': priority, 'notes': notes
            })
        new_req = InstrumentRequest.objects.create(
            requester=request.user,
            department=getattr(request.user, 'department', 'General Ward'),
            priority=priority, status='Requested', notes=notes,
        )
        for item, qty in valid_items:
            item.current_stock -= qty
            item.save()
            RequestItem.objects.create(request=new_req, inventory_item=item, quantity=qty)
        messages.success(request, f'Request REQ-{new_req.id:04d} submitted.')
        return redirect('nurse_dashboard')
    return render(request, 'nurse-create-request.html', {'instruments': instruments})
