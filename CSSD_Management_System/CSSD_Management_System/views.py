from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.db.models import F, Q
from django.utils import timezone

from .forms import EmailLoginForm, SterilizationBatchForm , InventoryItemForm
from .decorators import cssd_staff_required, admin_required, hospital_admin_required
from .models import (
    InstrumentRequest, RequestItem, InventoryItem,
    SterilizationBatch, CustomUser, Notification
)


def _notify_nurse(request_obj, message):
    Notification.objects.create(
        recipient=request_obj.requester,
        request=request_obj,
        message=message,
    )


def login_view(request):
    role_type = request.GET.get('role', 'staff')
    if role_type == 'nurse':
        template_name = 'nurse-login.html'
    elif role_type == 'admin':
        template_name = 'admin-login.html'
    else:
        template_name = 'staff-login.html'
    if request.method == 'POST':
        form = EmailLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
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
    if role == 'System Administrator':
        # Change this from redirect('/admin/') to your custom admin dashboard
        return redirect('admin_inventory_create') 
    elif role in ['CSSD Technician', 'Hospital Administrator']:
        return redirect('cssd_dashboard')
    elif role == 'Department Nurse':
        return redirect('nurse_dashboard')
    else:
        return HttpResponse(f"Role '{role}' not recognized.", status=403)


@login_required
@cssd_staff_required
def cssd_dashboard(request):
    show_pending_only = request.GET.get('filter') == 'pending'
    all_requests = InstrumentRequest.objects.all().order_by('-submitted_at')
    display_requests = all_requests.filter(status='Requested') if show_pending_only else all_requests[:10]

    pending_count     = all_requests.filter(status='Requested').count()
    in_progress_count = all_requests.filter(status__in=['Collected','Cleaned','Sterilized','Packed']).count()
    completed_count   = all_requests.filter(status='Delivered').count()
    alerts_count      = InventoryItem.objects.filter(current_stock__lt=3).count()

    context = {
        'staff_name': request.user.email.split('@')[0].capitalize(),
        'staff_role': getattr(request.user, 'role', 'CSSD Technician'),
        'stats': {
            'pending': pending_count,
            'in_progress': in_progress_count,
            'completed': completed_count,
            'alerts': alerts_count,
        },
        'requests': display_requests,
        'show_pending_only': show_pending_only,
    }
    return render(request, 'cssd-dashboard.html', context)


VALID_TRANSITIONS = {
    'Requested':  'Collected',
    'Collected':  'Cleaned',
    'Cleaned':    'Sterilized',
    'Sterilized': 'Packed',
    'Packed':     'Delivered',
}


@login_required
@cssd_staff_required
def cssd_request_detail(request, pk):
    req = get_object_or_404(InstrumentRequest, pk=pk)
    batches = SterilizationBatch.objects.all().order_by('-created_at')
    return render(request, 'cssd-request-details.html', {'req': req, 'batches': batches})


@login_required
@cssd_staff_required
def cssd_update_request_status(request, pk, status):
    req = get_object_or_404(InstrumentRequest, pk=pk)
    now = timezone.now()

    expected_next = VALID_TRANSITIONS.get(req.status)
    if expected_next != status:
        messages.error(request, f'Invalid transition: cannot move from "{req.status}" to "{status}". Expected: "{expected_next}".')
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

    req.status = status
    req.last_operator = request.user
    if status == 'Collected':
        req.collected_at = now
        _notify_nurse(req, f'REQ-{req.id:04d} has been collected by CSSD.')
    elif status == 'Cleaned':
        req.cleaned_at = now
        _notify_nurse(req, f'REQ-{req.id:04d} instruments have been cleaned.')
    elif status == 'Sterilized':
        req.sterilized_at = now
        _notify_nurse(req, f'REQ-{req.id:04d} instruments have been sterilized.')
    elif status == 'Packed':
        req.packed_at = now
        _notify_nurse(req, f'REQ-{req.id:04d} is packed and ready for delivery.')
    elif status == 'Delivered':
        req.delivered_at = now
        _notify_nurse(req, f'REQ-{req.id:04d} has been delivered.')

    req.save()
    return redirect('cssd_request_detail', pk=pk)


@login_required
@cssd_staff_required
def cssd_delete_request(request, pk):
    req = get_object_or_404(InstrumentRequest, pk=pk)
    req.delete()
    return redirect('cssd_dashboard')


@login_required
@cssd_staff_required
def cssd_inventory_alerts(request):
    all_alerts     = InventoryItem.objects.filter(current_stock__lt=3)
    total_alerts   = all_alerts.count()
    critical_count = all_alerts.filter(current_stock=0).count()
    return render(request, 'cssd-inventory-alerts.html', {
        'alerts': all_alerts,
        'total_alerts': total_alerts,
        'critical': critical_count,
        'low_stock': total_alerts - critical_count,
    })


@login_required
@cssd_staff_required
def cssd_batch_list(request):
    batches = SterilizationBatch.objects.all().order_by('-created_at')
    return render(request, 'cssd-batch-list.html', {'batches': batches})


@login_required
@cssd_staff_required
def cssd_batch_create(request):
    if request.method == 'POST':
        form = SterilizationBatchForm(request.POST)
        if form.is_valid():
            batch = form.save(commit=False)
            batch.operator = request.user
            batch.status = 'In Progress'
            batch.save()
            messages.success(request, f'Batch #{batch.id} created successfully.')
            return redirect('cssd_batch_detail', pk=batch.id)
    else:
        form = SterilizationBatchForm()
    return render(request, 'cssd-batch-create.html', {'form': form})


@login_required
@cssd_staff_required
def cssd_batch_detail(request, pk):
    batch = get_object_or_404(SterilizationBatch, pk=pk)
    linked_requests = InstrumentRequest.objects.filter(batch=batch)
    return render(request, 'cssd-batch-detail.html', {'batch': batch, 'linked_requests': linked_requests})


@login_required
def nurse_dashboard(request):
    all_requests    = InstrumentRequest.objects.filter(requester=request.user).order_by('-submitted_at')
    active_requests = all_requests.exclude(status='Delivered')

    unread_notifications = Notification.objects.filter(
        recipient=request.user, is_read=False
    ).order_by('-created_at')

    context = {
        'nurse_name': request.user.email.split('@')[0].capitalize(),
        'nurse_ward': getattr(request.user, 'department', 'General Ward'),
        'stats': {
            'total': all_requests.count(),
            'in_progress': all_requests.filter(status__in=['Collected','Cleaned','Sterilized','Packed']).count(),
            'urgent': all_requests.filter(priority='Urgent').count(),
            'delivered': all_requests.filter(status='Delivered').count(),
        },
        'requests': active_requests,
        'notifications': unread_notifications,
        'notif_count': unread_notifications.count(),
    }
    return render(request, 'nurse-dashboard.html', context)


@login_required
def nurse_mark_notifications_read(request):
    Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
    return redirect('nurse_dashboard')


@login_required
def nurse_request_detail(request, pk):
    req = get_object_or_404(InstrumentRequest, pk=pk)
    eta = req.get_eta()
    return render(request, 'nurse-request-details.html', {'req': req, 'eta': eta})


@login_required
def nurse_deliver_request(request, pk):
    req = get_object_or_404(InstrumentRequest, pk=pk)
    if req.requester != request.user:
        messages.error(request, 'Only the nurse who submitted this request can mark it as Delivered.')
        return redirect('nurse_request_detail', pk=pk)
    if req.status != 'Packed':
        messages.error(request, 'This request is not in Packed state and cannot be marked as Delivered.')
        return redirect('nurse_request_detail', pk=pk)
    req.status = 'Delivered'
    req.delivered_at = timezone.now()
    req.save()
    _notify_nurse(req, f'REQ-{req.id:04d} has been marked as Delivered.')
    return redirect('nurse_request_detail', pk=pk)


@login_required
def nurse_create_request(request):
    # Fetch instruments for the form
    instruments = InventoryItem.objects.all().order_by('category', 'name')
    
    if request.method == 'POST':
        priority = request.POST.get('priority', 'Normal')
        notes = request.POST.get('notes', '')
        
        # This list will hold tuples of (instrument_object, quantity) if they pass validation
        valid_items_to_create = []
        has_stock_error = False
        
        # 1. VALIDATION LOOP: Check all items before saving anything
        for item in instruments:
            qty_key = f'quantity_{item.id}'
            qty_val = request.POST.get(qty_key)
            
            if qty_val and qty_val.isdigit():
                qty = int(qty_val)
                if qty > 0:
                    if qty > item.current_stock:
                        # Add an error message for the specific item
                        messages.error(request, f"Insufficient stock for {item.name}. Requested: {qty}, Available: {item.current_stock}")
                        has_stock_error = True
                    else:
                        valid_items_to_create.append((item, qty))

        # 2. CHECK IF ANY ITEMS WERE SELECTED
        if not valid_items_to_create and not has_stock_error:
            messages.warning(request, "Please select at least one instrument with a valid quantity.")
            has_stock_error = True

        # 3. IF ERRORS EXIST: Render the same page (don't redirect) to show alerts
        if has_stock_error:
            return render(request, 'nurse-create-request.html', {
                'instruments': instruments,
                'priority': priority,
                'notes': notes
            })

        # 4. FINALIZATION: Create records only if the logic reached this point (no errors)
        new_req = InstrumentRequest.objects.create(
            requester=request.user,
            department=getattr(request.user, 'department', 'General Ward'),
            priority=priority,
            status='Requested',
            notes=notes,
        )
        
        for item, qty in valid_items_to_create:
            # Deduct from inventory
            item.current_stock -= qty
            item.save()
            
            # Create the link record
            RequestItem.objects.create(
                request=new_req, 
                inventory_item=item, 
                quantity=qty
            )

        messages.success(request, f"Request REQ-{new_req.id:04d} submitted and inventory updated.")
        return redirect('nurse_dashboard')
        
    return render(request, 'nurse-create-request.html', {'instruments': instruments})


@login_required
def nurse_sterile_stock(request):
    category_filter = request.GET.get('category', '')
    packed_items = InventoryItem.objects.filter(
        requestitem__request__status='Packed'
    ).distinct()
    if category_filter:
        packed_items = packed_items.filter(category=category_filter)
    categories = InventoryItem.objects.values_list('category', flat=True).distinct()
    return render(request, 'nurse-sterile-stock.html', {
        'items': packed_items,
        'categories': categories,
        'selected_category': category_filter,
    })


@login_required
@hospital_admin_required
def hospital_report(request):
    from datetime import date as date_type
    from django.db.models import Count
    date_str = request.GET.get('date', timezone.now().date().isoformat())
    try:
        report_date = date_type.fromisoformat(date_str)
    except ValueError:
        report_date = timezone.now().date()

    day_start = timezone.make_aware(timezone.datetime.combine(report_date, timezone.datetime.min.time()))
    day_end   = timezone.make_aware(timezone.datetime.combine(report_date, timezone.datetime.max.time()))

    batches_today    = SterilizationBatch.objects.filter(created_at__range=(day_start, day_end))
    requests_today   = InstrumentRequest.objects.filter(submitted_at__range=(day_start, day_end))
    sterilized_today = requests_today.filter(status__in=['Sterilized','Packed','Delivered'])
    operators        = batches_today.values('operator__email').annotate(count=Count('id'))

    return render(request, 'hospital-report.html', {
        'report_date': report_date,
        'total_batches': batches_today.count(),
        'total_sterilized': sterilized_today.count(),
        'operators': operators,
        'batches': batches_today,
        'date_str': date_str,
    })


@login_required
@hospital_admin_required
def hospital_audit(request):
    query = request.GET.get('q', '')
    results = []
    if query:
        clean_q = query.replace('REQ-', '').replace('req-', '').strip()
        results = InstrumentRequest.objects.filter(
            Q(id__icontains=clean_q) |
            Q(items__inventory_item__name__icontains=query)
        ).distinct().order_by('-submitted_at')
    return render(request, 'hospital-audit.html', {'results': results, 'query': query})


@login_required
@admin_required
def admin_inventory_create(request):
    if request.method == 'POST':
        form = InventoryItemForm(request.POST)
        if form.is_valid():
            item = form.save()
            messages.success(request, f"Instrument '{item.name}' registered successfully.")
            return redirect('cssd_inventory_alerts') # Or your inventory list
    else:
        form = InventoryItemForm()
    return render(request, 'admin-inventory-create.html', {'form': form})