from django.shortcuts import render, redirect
from django.contrib.auth import  login, logout
from django.contrib.auth.decorators import login_required
from .forms import EmailLoginForm
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from .models import InstrumentSet , RequestItem , InstrumentRequest , InventoryItem
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
        return redirect('nurse_dashboard')
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
    
    request = InstrumentRequest.objects.get(id = request_id)
    status = ['Requested' , 'Collected' , 'Cleaned' , 'Sterilized' , 'Packed' , 'Delivered']
    request_dict = {
            'req' : request,
            'status_order' : status,
            'current_status_index' : status.index(request.status) ,
            'items' :  RequestItem.objects.filter(request = request)
        }
    print(request_dict)
    
    return render(request , 'nurse-request-details.html' , request_dict)