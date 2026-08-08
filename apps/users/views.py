from rest_framework import viewsets

from .models import User
from .serializers import UserSerializer


class UserViewSet(viewsets.ModelViewSet):
    """
    Handles CRUD operations for User.
    """

    queryset = User.objects.all()
    serializer_class = UserSerializer