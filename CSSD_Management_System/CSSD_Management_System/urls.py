from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard_router, name='dashboard_router'),
    path('nurse_dashboard/' , views.nurse_dashboard , name = 'nurse_dashboard'),
    path('nurse_create_request/' , views.nurse_create_request , name='nurse_create_request'),
    path('save_instrument_request/' , views.save_instrument_request , name ='save_instrument_request'),
    path('nurse_request_details/<int:request_id>/' , views.nurse_request_details , name = 'nurse_request_details')
]
