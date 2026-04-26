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
    # US-24: Assign Operator to Batch
    path('dashboard/cssd/batches/', views.cssd_batch_list, name='cssd_batch_list'),
    path('dashboard/cssd/batches/create/', views.cssd_batch_create, name='cssd_batch_create'),
    path('dashboard/cssd/batches/<int:pk>/', views.cssd_batch_detail, name='cssd_batch_detail'),
]
