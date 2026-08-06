import uuid

from django.db import models
from apps.users.models import User

class Workspace(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    name = models.CharField(max_length=255)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owned_workspaces')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Workspace'
        verbose_name_plural = 'Workspaces'
        db_table = 'workspaces'

    def __str__(self):
        return self.name

class WorkspaceMember(models.Model):

    class Role(models.TextChoices):
        ADMIN = "admin", "Admin"
        EDITOR = "editor", "Editor"
        VIEWER = "viewer", "Viewer"

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name='members')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='workspace_memberships')
    role = models.CharField(max_length=10, choices=Role.choices, default=Role.VIEWER)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Workspace Member'
        verbose_name_plural = 'Workspace Members'
        db_table = 'workspace_members'
        # unique_together = ('workspace', 'user')
        constraints = [
            models.UniqueConstraint(fields=['workspace', 'user'], name='unique_workspace_user')
        ]

    def __str__(self):
        return f"{self.user} - {self.workspace} ({self.role})"