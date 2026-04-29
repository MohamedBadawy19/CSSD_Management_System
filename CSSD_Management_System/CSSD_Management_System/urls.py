from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard_router, name='dashboard_router'),
    path('dashboard/cssd/', views.cssd_dashboard, name='cssd_dashboard'),
    path('dashboard/cssd/request/<int:pk>/', views.cssd_request_detail, name='cssd_request_detail'),
    # US-19: Mark as Sterilized
    path('dashboard/cssd/request/<int:pk>/update/<str:status>/', views.cssd_update_request_status, name='cssd_update_request_status'),
    # Supporting: create batch so sterilization can proceed
    path('dashboard/cssd/batches/create/', views.cssd_batch_create, name='cssd_batch_create'),
    path('dashboard/nurse/', views.nurse_dashboard, name='nurse_dashboard'),
    path('nurse_create_request/', views.nurse_create_request, name='nurse_create_request'),
    path('nurse_request_details/<int:request_id>/', views.nurse_request_details, name='nurse_request_details'),
    path('save_instrument_request/', views.save_instrument_request, name='save_instrument_request'),
    path('requests/<int:request_id>/deliver/', views.mark_delivered, name='mark_delivered'),
    path('requests/<int:request_id>/mark_collected/',views.mark_collected,name='mark_collected'),
    path(
        'requests/<int:request_id>/mark_cleaned/',
        views.mark_cleaned,
        name='mark_cleaned',
    ),
    path(
        'requests/<int:request_id>/mark_sterilized/',
        views.mark_sterilized,
        name='mark_sterilized',
    ),
    path(
        'requests/<int:request_id>/mark_packed/',
        views.mark_packed,
        name='mark_packed',
    ),path(
        'cssd_request_details/<int:request_id>/',
        views.cssd_request_details,
        name='cssd_request_details',
    ),
    path(
        'nurse_sterile_stock/',
        views.nurse_sterile_stock,
        name='nurse_sterile_stock',
    ),
]
