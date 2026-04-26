# US-29: View Estimated Completion Time (ETA)
# This branch isolates only the ETA display feature.
# Nurses can view the estimated time remaining for their instrument request
# to complete the sterilization pipeline based on its current status.

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from django.utils import timezone
from datetime import timedelta

from .forms import EmailLoginForm
from .decorators import cssd_staff_required
from .models import InstrumentRequest, RequestItem, InventoryItem, Notification


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
def nurse_dashboard(request):
    all_requests = InstrumentRequest.objects.filter(requester=request.user).order_by('-submitted_at')
    unread = Notification.objects.filter(recipient=request.user, is_read=False).order_by('-created_at')

    # Annotate each active request with its ETA
    active_requests = all_requests.exclude(status='Delivered')
    requests_with_eta = [
        {'req': req, 'eta': _compute_eta(req)}
        for req in active_requests
    ]

    context = {
        'nurse_name': request.user.email.split('@')[0].capitalize(),
        'nurse_ward': getattr(request.user, 'department', 'General Ward'),
        'stats': {
            'total': all_requests.count(),
            'in_progress': all_requests.filter(status__in=['Collected', 'Cleaned', 'Sterilized', 'Packed']).count(),
            'urgent': all_requests.filter(priority='Urgent').count(),
            'delivered': all_requests.filter(status='Delivered').count(),
        },
        'requests_with_eta': requests_with_eta,
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

    return f'~{time_str} (ready by {eta_time.strftime("%I:%M %p")})'


@login_required
def nurse_request_detail(request, pk):
    """
    US-29: Displays detailed request info including the Estimated Completion Time.
    The ETA is computed live based on current status and last-updated timestamp.
    """
    req = get_object_or_404(InstrumentRequest, pk=pk)

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
