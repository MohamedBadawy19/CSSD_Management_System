# US-27: View Inventory Shortage Alerts
# This branch isolates only the inventory shortage alert feature.
# CSSD staff can view items whose current stock is at or below the minimum threshold.

from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse

from .forms import EmailLoginForm
from .decorators import cssd_staff_required
from .models import InstrumentRequest, InventoryItem, Notification


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

    return render(request, 'cssd-inventory-alerts.html', {
        'alert_data': alert_data,
        'shortage_count': shortage_items.count(),
        'categories': categories,
        'selected_category': category_filter,
    })
