from django.db import IntegrityError, transaction
from rest_framework.decorators import action
from django.db.models import Count
from rest_framework import status
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from .models import Workspace, WorkspaceMember
from .serializers import (
    WorkspaceSerializer,
    WorkspaceMemberSerializer,
    AddMemberSerializer,
)

class WorkspaceViewSet(ModelViewSet):
    """
    Handles CRUD operations for Workspace.
    """

    queryset = Workspace.objects.select_related("owner").annotate(
        member_count=Count("members")
    )
    serializer_class = WorkspaceSerializer

    def create(self, request, *args, **kwargs):
        """Create a new workspace and add the owner as an admin member."""

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            with transaction.atomic():
                workspace = serializer.save()

                # Add the owner as an admin member
                WorkspaceMember.objects.create(
                    workspace=workspace,
                    user=workspace.owner,
                    role=WorkspaceMember.Role.ADMIN,
                )

            return Response(
                WorkspaceSerializer(workspace).data,
                status=status.HTTP_201_CREATED,
            )
        except IntegrityError:
            return Response(
                {"detail": "Failed to create workspace."},
                status=status.HTTP_409_CONFLICT,
            )

    @action(detail=True, methods=["post", "get"], url_path="members")
    def members(self, request, pk=None):
        """Add a member to workspace with a specific role."""

        workspace = self.get_object()

        if request.method == "POST":
            serializer = AddMemberSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            try:
                with transaction.atomic():
                    member = WorkspaceMember.objects.create(
                        workspace=workspace,
                        user=serializer.validated_data["user"],
                        role=serializer.validated_data["role"],
                    )
            except IntegrityError:
                return Response(
                    {"detail": "User is already a member of this workspace."},
                    status=status.HTTP_409_CONFLICT,
                )

            return Response(
                WorkspaceMemberSerializer(member).data,
                status=status.HTTP_201_CREATED,
            )
        
        elif request.method == "GET":
            members = workspace.members.select_related("user").all()
            serializer = WorkspaceMemberSerializer(members, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)


