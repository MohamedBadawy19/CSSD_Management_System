from django.shortcuts import render, redirect
from django.contrib.auth import  login, logout
from django.contrib.auth.decorators import login_required
from .forms import EmailLoginForm
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

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
