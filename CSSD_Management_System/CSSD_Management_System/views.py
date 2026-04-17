from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from .forms import EmailLoginForm
from .decorators import cssd_staff_required
from django.http import HttpResponse

def login_view(request):
    # Determine which template to show based on a URL parameter
    role_type = request.GET.get('role', 'staff')
    template_name = 'nurse-login.html' if role_type == 'nurse' else 'staff-login.html'

    if request.method == 'POST':
        form = EmailLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('dashboard_router')
    else:
        form = EmailLoginForm()
    
    # Render the specific role-based template
    return render(request, template_name, {'form': form})

def home(request):
    # Instead of a redirect, render your selection page
    return render(request, 'index.html')

def logout_view(request):
    logout(request)
    return redirect('login')

@login_required
def dashboard_router(request):
    """
    FR-02: Role-Based Dashboard Routing
    Detects the user’s role and routes them to their corresponding dashboard.
    """
    role = request.user.role
    if role in ['CSSD Technician', 'System Administrator', 'Hospital Administrator']:
        return redirect('cssd_dashboard')
    elif role == 'Department Nurse':
        return redirect('nurse_dashboard')
    else:
        return HttpResponse(f"Role '{role}' not found. Please contact admin.", status=403)

from django.db.models import F
from .models import InstrumentRequest, RequestItem, InventoryItem

@login_required
@cssd_staff_required
def cssd_dashboard(request):
    """
    Dashboard for CSSD Staff (Technicians, Admins, etc.)
    Blocked for Nurses.
    """
    recent_requests = InstrumentRequest.objects.all().order_by('-submitted_at')
    
    pending_count = InstrumentRequest.objects.filter(status='Requested').count()
    in_progress_count = InstrumentRequest.objects.filter(status__in=['Collected', 'Cleaned', 'Sterilized', 'Packed']).count()
    completed_count = InstrumentRequest.objects.filter(status='Delivered').count()
    alerts_count = InventoryItem.objects.filter(current_stock__lte=F('min_threshold')).count()

    context = {
        'staff_name': request.user.email.split('@')[0].capitalize(),
        'staff_role': getattr(request.user, 'role', 'CSSD Technician'),
        'stats': {
            'pending': pending_count,
            'in_progress': in_progress_count,
            'completed': completed_count,
            'alerts': alerts_count,
        },
        'requests': recent_requests[:10]
    }
    return render(request, 'cssd-dashboard.html', context)

@login_required
def nurse_dashboard(request):
    """
    Dashboard for Department Nurses.
    """
    my_requests = InstrumentRequest.objects.filter(requester=request.user).order_by('-submitted_at')
    
    total_count = my_requests.count()
    in_progress_count = my_requests.filter(status__in=['Collected', 'Cleaned', 'Sterilized', 'Packed']).count()
    urgent_count = my_requests.filter(priority='Urgent').count()
    delivered_count = my_requests.filter(status='Delivered').count()

    context = {
        'nurse_name': request.user.email.split('@')[0].capitalize(),
        'nurse_ward': getattr(request.user, 'department', 'General Ward'),
        'stats': {
            'total': total_count,
            'in_progress': in_progress_count,
            'urgent': urgent_count,
            'delivered': delivered_count,
        },
        'requests': my_requests[:10]
    }
    return render(request, 'nurse-dashboard.html', context)

@login_required
def nurse_request_detail(request, pk):
    req = InstrumentRequest.objects.get(pk=pk) # In real app use get_object_or_404
    return render(request, 'nurse-request-details.html', {'req': req})

@login_required
@cssd_staff_required
def cssd_request_detail(request, pk):
    req = InstrumentRequest.objects.get(pk=pk)
    return render(request, 'cssd-request-details.html', {'req': req})

@login_required
@cssd_staff_required
def cssd_update_request_status(request, pk, status):
    req = InstrumentRequest.objects.get(pk=pk)
    req.status = status
    import django.utils.timezone as tz
    now = tz.now()
    if status == 'Collected': req.collected_at = now
    elif status == 'Cleaned': req.cleaned_at = now
    elif status == 'Sterilized': req.sterilized_at = now
    elif status == 'Packed': req.packed_at = now
    elif status == 'Delivered': req.delivered_at = now
    req.save()
    return redirect('cssd_request_detail', pk=pk)

@login_required
@cssd_staff_required
def cssd_delete_request(request, pk):
    req = InstrumentRequest.objects.get(pk=pk)
    req.delete()
    return redirect('cssd_dashboard')

@login_required
def nurse_create_request(request):
    instruments = InventoryItem.objects.filter(category='Instruments')
    if request.method == 'POST':
        priority = request.POST.get('priority', 'Normal')
        notes = request.POST.get('notes', '')
        
        new_req = InstrumentRequest.objects.create(
            requester=request.user,
            department=getattr(request.user, 'department', 'General Ward'),
            priority=priority,
            status='Requested',
            notes=notes
        )
        
        for item in instruments:
            qty_key = f'quantity_{item.id}'
            if request.POST.get(qty_key) and request.POST[qty_key].isdigit():
                qty = int(request.POST[qty_key])
                if qty > 0:
                    RequestItem.objects.create(request=new_req, inventory_item=item, quantity=qty)
                    
        return redirect('nurse_dashboard')

    return render(request, 'nurse-create-request.html', {'instruments': instruments})

@login_required
@cssd_staff_required
def cssd_inventory_alerts(request):
    all_alerts = InventoryItem.objects.filter(current_stock__lte=F('min_threshold'))
    
    total_alerts = all_alerts.count()
    critical_count = all_alerts.filter(current_stock__lt=F('min_threshold') / 3).count() # rough approximation for 'critical'
    
    return render(request, 'cssd-inventory-alerts.html', {
        'alerts': all_alerts,
        'total_alerts': total_alerts,
        'critical': critical_count,
        'low_stock': total_alerts - critical_count
    })

