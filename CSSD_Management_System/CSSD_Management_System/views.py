# US-20: Mark Instrument Request as Delivered
# This branch isolates only the "Mark as Delivered" feature.
# The NURSE confirms delivery of a Packed instrument request.

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from django.utils import timezone

from .forms import EmailLoginForm, InventoryItemForm
from .decorators import cssd_staff_required
from .models import InstrumentRequest, RequestItem, InventoryItem, Notification


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
def nurse_request_detail(request, pk):
    req = get_object_or_404(InstrumentRequest, pk=pk)
    return render(request, 'nurse-request-details.html', {'req': req, 'eta': req.get_eta()})


# ---------------------------------------------------------------------------
# US-20: Mark as Delivered  ← FEATURE
# ---------------------------------------------------------------------------

@login_required
def nurse_deliver_request(request, pk):
    """
    US-20: The nurse who submitted the request confirms delivery once it is Packed.
    Only the Packed → Delivered transition is permitted.
    Only the original requester can confirm delivery.
    """
    req = get_object_or_404(InstrumentRequest, pk=pk)

    if req.requester != request.user:
        messages.error(request, 'Only the nurse who submitted this request can mark it as Delivered.')
        return redirect('nurse_request_detail', pk=pk)

    if req.status != 'Packed':
        messages.error(request, f"Cannot mark as Delivered. Current status: '{req.status}'. Must be Packed.")
        return redirect('nurse_request_detail', pk=pk)

    req.status = 'Delivered'
    req.delivered_at = timezone.now()
    req.save()
    _notify_nurse(req, f'REQ-{req.id:04d} has been confirmed as Delivered.')
    messages.success(request, f'REQ-{req.id:04d} marked as Delivered.')
    return redirect('nurse_request_detail', pk=pk)


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
