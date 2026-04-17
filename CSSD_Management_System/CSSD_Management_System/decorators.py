from django.http import HttpResponseForbidden
from functools import wraps

def cssd_staff_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return HttpResponseForbidden("Authentication Required")
        
        # FR-03: explicitly block users with the 'Nurse' role from CSSD specific endpoints
        if request.user.role == 'Department Nurse':
            return HttpResponseForbidden("Access Denied: Nurses are not allowed to access CSSD specific endpoints.")
        
        return view_func(request, *args, **kwargs)
    return _wrapped_view
