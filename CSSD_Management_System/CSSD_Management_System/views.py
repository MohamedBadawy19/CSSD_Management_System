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

@login_required
@cssd_staff_required
def cssd_dashboard(request):
    """
    Dashboard for CSSD Staff (Technicians, Admins, etc.)
    Blocked for Nurses.
    """
    return HttpResponse(f"<h1>CSSD Staff Dashboard</h1><p>Welcome, {request.user.email} (Role: {request.user.role})</p><a href='/logout/'>Logout</a>")

@login_required
def nurse_dashboard(request):
    """
    Dashboard for Department Nurses.
    """
    return HttpResponse(f"<h1>Department Nurse Dashboard</h1><p>Welcome, {request.user.email} (Role: {request.user.role})</p><a href='/logout/'>Logout</a>")

