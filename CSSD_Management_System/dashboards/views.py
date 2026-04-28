from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import redirect, render

from department_requests.models import InstrumentRequest, InventoryItem, RequestItem


@login_required
def dashboard_router(request):
    role = request.user.role

    if role in ["CSSD Technician", "System Administrator", "Hospital Administrator"]:
        filter_status = request.GET.get("filter", "")
        all_requests = InstrumentRequest.objects.prefetch_related(
            "items__inventory_item", "requester"
        ).order_by("-submitted_at")
        display_requests = (
            all_requests.filter(status="Requested")
            if filter_status == "pending"
            else all_requests
        )

        stat_pending = all_requests.filter(status="Requested").count()
        stat_active = all_requests.filter(
            status__in=["Collected", "Cleaned", "Sterilized", "Packed"]
        ).count()
        stat_alerts = InventoryItem.objects.filter(current_stock__lt=3).count()

        status_order = [
            "Requested",
            "Collected",
            "Cleaned",
            "Sterilized",
            "Packed",
            "Delivered",
        ]
        urgent_reqs = all_requests.filter(priority="Urgent").exclude(status="Delivered")
        eta_text, eta_desc = "No urgent", "All clear"
        if urgent_reqs.exists():
            mins_candidates = [
                max(0, (len(status_order) - 1 - status_order.index(r.status)) * 20)
                if r.status in status_order
                else (len(status_order) - 1) * 20
                for r in urgent_reqs
            ]
            mins = min(mins_candidates)
            eta_text = f"~{mins} min" if mins < 60 else f"~{mins // 60:.1f} hr"
            eta_desc = f"{urgent_reqs.count()} urgent request(s) pending"

        return render(
            request,
            "cssd-dashboard.html",
            {
                "requests": display_requests,
                "filter_status": filter_status,
                "stat_pending": stat_pending,
                "stat_active": stat_active,
                "stat_alerts": stat_alerts,
                "eta_text": eta_text,
                "eta_desc": eta_desc,
            },
        )

    if role == "Department Nurse":
        return redirect("nurse_dashboard")
    return HttpResponse(f"Role '{role}' not found. Please contact admin.", status=403)


@login_required
def nurse_dashboard(request):
    requests = InstrumentRequest.objects.filter(requester=request.user)
    final_requests = [
        {
            "id": req.id,
            "instruments": RequestItem.objects.filter(request=req),
            "priority": req.priority,
            "status": req.status,
            "department": req.department,
            "notes": req.notes,
        }
        for req in requests
    ]

    return render(
        request,
        "nurse-dashboard.html",
        {
            "requests": final_requests,
            "total": requests.count(),
            "in_progress": requests.filter(
                status__in=["Collected", "Cleaned", "Sterilized", "Packed"]
            ).count(),
            "urgent": requests.filter(priority="Urgent").count(),
            "delivered": requests.filter(status="Delivered").count(),
        },
    )

# Create your views here.
