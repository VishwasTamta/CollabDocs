import re
from rest_framework import serializers

from .models import User


class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ("id", "first_name", "last_name", "email", "phone", "created_at")
        read_only_fields = ("id", "created_at")

        def validate_phone(self, value):
            # Phone can be digits with use regex to validate the phone number format
            
            pattern = r'^\+?\d{10,15}$'

            if not re.match(pattern, value):
                raise serializers.ValidationError("Phone number must be between 10 and 15 digits, optionally starting with +.")

            return value