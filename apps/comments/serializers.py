from rest_framework import serializers

from apps.workspaces.models import WorkspaceMember

from .models import Comment


class CommentSerializer(serializers.ModelSerializer):

    author_name = serializers.SerializerMethodField()
    reply_count = serializers.SerializerMethodField()
    replies = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = (
            "id",
            "document",
            "author",
            "author_name",
            "content",
            "parent",
            "created_at",
            "reply_count",
            "replies",
        )
        read_only_fields = (
            "id",
            "created_at",
            "author_name",
            "reply_count",
            "replies",
        )

    def validate_content(self, value):
        if not value.strip():
            raise serializers.ValidationError("Comment content cannot be empty.")
        return value.strip()

    def validate(self, attrs):
        """A reply belongs to its parent's document, and authors must be members."""

        document = attrs.get("document") or getattr(self.instance, "document", None)
        author = attrs.get("author") or getattr(self.instance, "author", None)
        parent = attrs.get("parent", getattr(self.instance, "parent", None))

        if parent and document and parent.document_id != document.id:
            raise serializers.ValidationError(
                {
                    "parent": (
                        "A reply must belong to the same document as the comment "
                        "it replies to."
                    )
                }
            )

        if parent and self.instance and parent.id == self.instance.id:
            raise serializers.ValidationError(
                {"parent": "A comment cannot be a reply to itself."}
            )

        if document and author:
            is_member = WorkspaceMember.objects.filter(
                workspace_id=document.workspace_id,
                user=author,
            ).exists()

            if not is_member:
                raise serializers.ValidationError(
                    {
                        "author": (
                            f"{author} is not a member of the workspace this "
                            "document belongs to and cannot comment on it."
                        )
                    }
                )

        return attrs

    def get_author_name(self, obj):
        return str(obj.author) if obj.author else None

    def get_reply_count(self, obj):
        return obj.replies.count()

    def get_replies(self, obj):
        """Nest the reply tree under each comment. Empty for a leaf."""

        replies = obj.replies.select_related("author").order_by("created_at")

        return CommentSerializer(replies, many=True, context=self.context).data
