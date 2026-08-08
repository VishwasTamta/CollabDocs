from rest_framework import serializers

from .models import Workspace, WorkspaceMember


class WorkspaceSerializer(serializers.ModelSerializer):

    members_count = serializers.SerializerMethodField()

    class Meta:
        model = Workspace
        fields = (
            "id",
            "name",
            "owner",
            "created_at",
            "members_count",
        )
        read_only_fields = (
            "id",
            "created_at",
            "members_count",
        )

    def validate_name(self, value):
        if len(value.strip()) < 3:
            raise serializers.ValidationError(
                "Workspace name must be at least 3 characters."
            )
        return value

    def get_members_count(self, obj):
        return getattr(obj, "member_count", obj.members.count())


class WorkspaceMemberSerializer(serializers.ModelSerializer):

    class Meta:
        model = WorkspaceMember
        fields = "__all__"

class AddMemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkspaceMember
        fields = ("user", "role")

    