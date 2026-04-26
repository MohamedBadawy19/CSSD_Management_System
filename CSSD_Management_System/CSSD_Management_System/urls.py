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
    path('dashboard/nurse/', views.nurse_dashboard, name='nurse_dashboard'),
    path('dashboard/nurse/create/', views.nurse_create_request, name='nurse_create_request'),
    # US-29: View Estimated Completion Time
    path('dashboard/nurse/request/<int:pk>/', views.nurse_request_detail, name='nurse_request_detail'),
]
