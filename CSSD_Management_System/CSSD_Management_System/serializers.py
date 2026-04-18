from rest_framework import serializers
from django.contrib.auth import get_user_model

CustomUser = get_user_model()

class UserCreationSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['email', 'password', 'role', 'department']
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def create(self, validated_data):
        # We use create_user to correctly hash the password.
        # Role and department are provided since we verified the admin is doing this via permissions.
        user = CustomUser.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            role=validated_data['role'],
            department=validated_data.get('department', '')
        )
        return user
