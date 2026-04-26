# US-24: Assign Operator to Sterilization Batch
# This branch isolates only the batch creation and operator assignment feature.

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse

from .forms import EmailLoginForm, SterilizationBatchForm
from .decorators import cssd_staff_required
from .models import InstrumentRequest, InventoryItem, SterilizationBatch, Notification


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
    """
    US-24: Creates a new sterilization batch and assigns the current user as operator.
    The logged-in CSSD technician is automatically set as the batch operator.
    """
    if request.method == 'POST':
        form = SterilizationBatchForm(request.POST)
        if form.is_valid():
            batch = form.save(commit=False)
            batch.operator = request.user   # ← assigns the operator
            batch.save()
            messages.success(request, f'Batch #{batch.id} created. Operator: {request.user.email}')
            return redirect('cssd_batch_detail', pk=batch.id)
    else:
        form = SterilizationBatchForm()
    return render(request, 'cssd-batch-create.html', {'form': form})


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
