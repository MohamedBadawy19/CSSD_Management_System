from django.http import HttpResponseForbidden
from functools import wraps

def cssd_staff_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return HttpResponseForbidden("Authentication Required")
        if request.user.role == 'Department Nurse':
            return HttpResponseForbidden("Access Denied: Nurses cannot access CSSD endpoints.")
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def admin_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return HttpResponseForbidden("Authentication Required")
        if request.user.role != 'System Administrator':
            return HttpResponseForbidden("Access Denied: System Administrators only.")
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def hospital_admin_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return HttpResponseForbidden("Authentication Required")
        if request.user.role not in ('Hospital Administrator', 'System Administrator'):
            return HttpResponseForbidden("Access Denied: Hospital Administrators only.")
        return view_func(request, *args, **kwargs)
    return _wrapped_view
