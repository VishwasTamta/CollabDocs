from rest_framework import serializers

from apps.users.models import User
from apps.workspaces.models import WorkspaceMember

from .models import Document, DocumentVersion


class DocumentVersionSerializer(serializers.ModelSerializer):

    saved_by_name = serializers.SerializerMethodField()

    class Meta:
        model = DocumentVersion
        fields = (
            "id",
            "document",
            "version_number",
            "content",
            "saved_by",
            "saved_by_name",
            "saved_at",
        )
        read_only_fields = fields

    def get_saved_by_name(self, obj):
        return str(obj.saved_by) if obj.saved_by else None


class DocumentSerializer(serializers.ModelSerializer):

    version_count = serializers.SerializerMethodField()
    latest_version = serializers.SerializerMethodField()
    tag_names = serializers.SerializerMethodField()

    # Who performed this particular save. Not stored on Document itself, it is
    # popped by the viewset and written onto the DocumentVersion row.
    saved_by = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        write_only=True,
        required=False,
        allow_null=True,
    )

    class Meta:
        model = Document
        fields = (
            "id",
            "title",
            "content",
            "workspace",
            "created_by",
            "status",
            "updated_at",
            "version_count",
            "latest_version",
            "tag_names",
            "saved_by",
        )
        read_only_fields = (
            "id",
            "updated_at",
            "version_count",
            "latest_version",
            "tag_names",
        )

    def validate_title(self, value):
        if len(value.strip()) < 3:
            raise serializers.ValidationError(
                "Document title must be at least 3 characters."
            )
        return value.strip()

    def validate(self, attrs):
        """The author of a document must belong to the workspace it lives in."""

        workspace = attrs.get("workspace") or getattr(
            self.instance, "workspace", None
        )
        created_by = attrs.get("created_by") or getattr(
            self.instance, "created_by", None
        )

        if workspace and created_by:
            is_member = WorkspaceMember.objects.filter(
                workspace=workspace,
                user=created_by,
            ).exists()

            if not is_member:
                raise serializers.ValidationError(
                    {
                        "created_by": (
                            f"{created_by} is not a member of workspace "
                            f"'{workspace}'. Add them to the workspace first."
                        )
                    }
                )

        return attrs

    def get_version_count(self, obj):
        return getattr(obj, "version_total", obj.versions.count())

    def get_latest_version(self, obj):
        version = obj.versions.order_by("-version_number").first()

        if version is None:
            return None

        return {
            "id": version.id,
            "version_number": version.version_number,
            "saved_at": version.saved_at,
        }

    def get_tag_names(self, obj):
        return list(obj.tags.values_list("name", flat=True))
