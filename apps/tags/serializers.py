from rest_framework import serializers

from apps.users.models import User

from .models import Tag


class TagSerializer(serializers.ModelSerializer):

    document_count = serializers.SerializerMethodField()

    # Declared without validators so DRF does not attach its automatic
    # UniqueValidator. That validator would reject a duplicate name with a 400
    # before the request reached the database; letting the unique constraint
    # raise instead lets the view answer 409, which is the right code for a
    # resource that already exists.
    name = serializers.CharField(max_length=100, validators=[])

    class Meta:
        model = Tag
        fields = (
            "id",
            "name",
            "document_count",
        )
        read_only_fields = (
            "id",
            "document_count",
        )

    def validate_name(self, value):
        """Normalise before saving so the unique constraint actually bites."""

        normalized = value.strip().lower()

        if len(normalized) < 2:
            raise serializers.ValidationError(
                "Tag name must be at least 2 characters."
            )

        if " " in normalized:
            raise serializers.ValidationError(
                "Tag name cannot contain spaces. Use a hyphen instead."
            )

        return normalized

    def get_document_count(self, obj):
        return getattr(obj, "document_total", obj.documents.count())


class AttachTagsSerializer(serializers.Serializer):
    """Validates the body of POST /api/documents/{id}/tags/."""

    tags = serializers.ListField(
        child=serializers.CharField(max_length=100),
        required=False,
        allow_empty=True,
    )
    tag_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=False,
        allow_empty=True,
    )
    actor = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        required=False,
        allow_null=True,
    )

    def validate(self, attrs):
        names = attrs.get("tags") or []
        tag_ids = attrs.get("tag_ids") or []

        if not names and not tag_ids:
            raise serializers.ValidationError(
                "Provide at least one tag name in 'tags' or one id in 'tag_ids'."
            )

        cleaned = []
        for name in names:
            normalized = name.strip().lower()

            if len(normalized) < 2:
                raise serializers.ValidationError(
                    {
                        "tags": (
                            f"'{name}' is too short. "
                            "Tag names need at least 2 characters."
                        )
                    }
                )

            if " " in normalized:
                raise serializers.ValidationError(
                    {
                        "tags": (
                            f"'{name}' cannot contain spaces. Use a hyphen instead."
                        )
                    }
                )

            if normalized not in cleaned:
                cleaned.append(normalized)

        attrs["tags"] = cleaned

        return attrs
