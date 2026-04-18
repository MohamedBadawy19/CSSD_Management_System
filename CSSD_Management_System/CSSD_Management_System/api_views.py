from rest_framework.generics import CreateAPIView
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model
from .serializers import UserCreationSerializer
from .permissions import IsSystemAdministrator

CustomUser = get_user_model()

class UserCreateAPIView(CreateAPIView):
    """
    Endpoint for creating users. 
    Accessible ONLY to System Administrators.
    """
    queryset = CustomUser.objects.all()
    serializer_class = UserCreationSerializer
    permission_classes = [IsAuthenticated, IsSystemAdministrator]
