from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard_router, name='dashboard_router'),

    # CSSD
    path('dashboard/cssd/', views.cssd_dashboard, name='cssd_dashboard'),
    path('dashboard/cssd/request/<int:pk>/', views.cssd_request_detail, name='cssd_request_detail'),
    path('dashboard/cssd/request/<int:pk>/update/<str:status>/', views.cssd_update_request_status, name='cssd_update_request_status'),
    path('dashboard/cssd/request/<int:pk>/delete/', views.cssd_delete_request, name='cssd_delete_request'),
    path('dashboard/cssd/alerts/', views.cssd_inventory_alerts, name='cssd_inventory_alerts'),
    path('dashboard/cssd/batches/', views.cssd_batch_list, name='cssd_batch_list'),
    path('dashboard/cssd/batches/create/', views.cssd_batch_create, name='cssd_batch_create'),
    path('dashboard/cssd/batches/<int:pk>/', views.cssd_batch_detail, name='cssd_batch_detail'),

    # Nurse
    path('dashboard/nurse/', views.nurse_dashboard, name='nurse_dashboard'),
    path('dashboard/nurse/request/<int:pk>/', views.nurse_request_detail, name='nurse_request_detail'),
    path('dashboard/nurse/request/<int:pk>/deliver/', views.nurse_deliver_request, name='nurse_deliver_request'),
    path('dashboard/nurse/create/', views.nurse_create_request, name='nurse_create_request'),
    path('dashboard/nurse/sterile-stock/', views.nurse_sterile_stock, name='nurse_sterile_stock'),
    path('dashboard/nurse/notifications/read/', views.nurse_mark_notifications_read, name='nurse_mark_notifications_read'),

    # Hospital Admin
    path('dashboard/hospital/report/', views.hospital_report, name='hospital_report'),
    path('dashboard/hospital/audit/', views.hospital_audit, name='hospital_audit'),
    path('dashboard/admin/inventory/create/', views.admin_inventory_create, name='admin_inventory_create'),
]