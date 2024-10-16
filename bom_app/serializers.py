from rest_framework import serializers
from .models import Item
from django.contrib.auth import get_user_model

User = get_user_model()

class RegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username','password']
        extra_kwargs ={'password': {'write_only':True}}

    def create(self,validated_data):
        user =User.objects.create_user(
            username = validated_data['username'],
            password = validated_data['password'],
  
        )
        return user



class ItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Item
        fields = '__all__'
