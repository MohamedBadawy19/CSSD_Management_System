from django.http import HttpRequest 
from django.shortcuts import render 
from django.views.decorators.csrf import csrf_exempt
import os 

templates_path = os.path.join( os.path.dirname(__file__), 'templates')



# HTML FILES PATHS
main_path = os.path.join(templates_path , 'home.html')

@csrf_exempt
def home(request):
    return render(request , main_path )