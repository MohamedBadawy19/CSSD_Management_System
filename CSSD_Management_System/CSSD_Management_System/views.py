from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import  login, logout
from django.contrib.auth.decorators import login_required
from .forms import EmailLoginForm
from django.http import HttpResponse , HttpResponseForbidden, HttpResponseNotAllowed
from django.views.decorators.csrf import csrf_exempt
from .models import InstrumentSet , RequestItem , InstrumentRequest , InventoryItem, Notification
from .decorators import cssd_staff_required
from django.contrib import messages
from django.utils import timezone
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
    
    # Render the specific role-based template
    return render(request, template_name, {'form': form})

def home(request):
    # Instead of a redirect, render your selection page
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
    Detects the user’s role and routes them to their corresponding dashboard.
    """
    role = request.user.role
    
    if role in ['CSSD Technician', 'System Administrator', 'Hospital Administrator']:
        return render(request , 'cssd-dashboard.html')
    elif role == 'Department Nurse':
        return render(request , 'nurse-dashboard.html')
    else:
        return HttpResponse(f"Role '{role}' not found. Please contact admin.", status=403)



@login_required
def nurse_dashboard(request):
    final_requests = []

    requests = InstrumentRequest.objects.filter(requester = request.user)
    
    for request in requests:
        instruments = RequestItem.objects.filter(request = request)
        priority = request.priority
        status = request.status
        department = request.department
        notes = request.notes
        id = request.id
        request_dict = {
            'id' : id,
            'instruments' : instruments,
            'priority' : priority,
            'status' : status,
            'department' : department,
            'notes' : notes,
            
        }
        final_requests.append(request_dict)

    total = len(requests)
    in_progress = len(requests.filter(status__in=['Collected','Cleaned','Sterilized','Packed']))
    urgent = len(requests.filter(priority='Urgent'))
    delivered = len(requests.filter(priority='Delivered'))

    context = {
        'requests': final_requests,
        'total': total,
        'in_progress': in_progress,
        'urgent': urgent,
        'delivered': delivered,
    }

    return render(request , 'nurse-dashboard.html'  , context)
def get_instruments():
    instruments = []
    for instrument in InventoryItem.objects.all():
        instrument_dict = {
            'name' : instrument.name,
            'category' : instrument.category,
            'current_stock' : instrument.current_stock,
            'min_threshold' : instrument.min_threshold,

        }

        instruments.append(instrument_dict)
    return instruments 

@login_required
def nurse_create_request(request):
    
        
    return render(request , 'nurse-create-request.html' , {'instruments' : get_instruments()})


@csrf_exempt
def save_instrument_request(request):
    if request.method == 'POST':

        instruments = request.POST.getlist('instruments')
        priority = request.POST.get('priority')
        notes = request.POST.get('notes')

        new_request = InstrumentRequest.objects.create(
            requester = request.user,
            priority = priority,
            department = request.user.department,
            notes = notes,
            submitted_at = datetime.datetime.now()
        )

        for instrument in instruments:
            quantity = int(request.POST.get("quantity_" + instrument))
            database_instrument = InventoryItem.objects.get(name = instrument)
            
            if quantity > database_instrument.current_stock:
                return render(request , 'nurse-create-request.html' , {'instruments' : get_instruments() , 'warning': f'instrument {instrument} has current_stock : {database_instrument.current_stock}' })

            RequestItem.objects.create(
                request = new_request,
                inventory_item = database_instrument,
                quantity = quantity
            )
            database_instrument.current_stock -= quantity
            database_instrument.save()
    return redirect('nurse_create_request')
def nurse_request_details(request , request_id):
    
    
    instrument_request = InstrumentRequest.objects.get(id = request_id)
    if request.user == instrument_request.requester:

        status = ['Requested' , 'Collected' , 'Cleaned' , 'Sterilized' , 'Packed' , 'Delivered']
        request_dict = {
                'req' : instrument_request,
                'status_order' : status,
                'current_status_index' : status.index(instrument_request.status) ,
                'items' :  RequestItem.objects.filter(request = instrument_request)
            }
        return render(request , 'nurse-request-details.html' , request_dict)

    return HttpResponseForbidden("Access Denined")

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
    US-17: Allows a CSSD technician to mark an InstrumentRequest as Collected.
    Only the Requested → Collected transition is permitted in this branch.
    Only POST requests are accepted; GET returns 405.
    """
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])

    req = get_object_or_404(InstrumentRequest, pk=pk)

    if status != 'Collected':
        messages.error(request, f"This branch only supports marking as Collected. Got: '{status}'.")
        return redirect('cssd_request_detail', pk=pk)

    if req.status != 'Requested':
        messages.error(request, f"Can only collect a Requested item. Current status: '{req.status}'.")
        return redirect('cssd_request_detail', pk=pk)

    req.status = 'Collected'
    req.collected_at = timezone.now()
    req.last_operator = request.user
    req.save()
    _notify_nurse(req, f'REQ-{req.id:04d} has been collected by CSSD.')
    messages.success(request, f'REQ-{req.id:04d} marked as Collected.')
    return redirect('cssd_request_detail', pk=pk)
