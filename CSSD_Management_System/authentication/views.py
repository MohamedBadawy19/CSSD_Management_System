from django.contrib.auth import login, logout
from django.shortcuts import redirect, render

from .forms import EmailLoginForm


def home(request):
    if request.user.is_authenticated:
        return redirect("dashboard_router")
    return render(request, "index.html")


def login_view(request):
    role_type = request.POST.get("role") or request.GET.get("role", "staff")
    template_name = "nurse-login.html" if role_type == "nurse" else "staff-login.html"

    if request.method == "POST":
        form = EmailLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect("dashboard_router")
    else:
        form = EmailLoginForm()

    return render(
        request,
        template_name,
        {
            "form": form,
            "role_type": role_type,
        },
    )


def logout_view(request):
    logout(request)
    return redirect("home")

# Create your views here.
