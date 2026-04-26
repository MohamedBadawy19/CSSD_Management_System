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
    # US-21: Mark as Packed
    path('dashboard/cssd/request/<int:pk>/update/<str:status>/', views.cssd_update_request_status, name='cssd_update_request_status'),
    path('dashboard/nurse/', views.nurse_dashboard, name='nurse_dashboard'),
    path('dashboard/nurse/create/', views.nurse_create_request, name='nurse_create_request'),
]
