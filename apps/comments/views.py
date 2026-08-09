from django.db import transaction
from django.db.models import Count, Q
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from apps.auditlogs.models import AuditLog
from apps.common.utils import parse_timestamp
from apps.documents.models import Document

from .models import Comment
from .serializers import CommentSerializer


class CommentViewSet(ModelViewSet):
    """
    Handles CRUD operations for Comment.

    A comment with no parent is a top-level comment; a comment with a parent is
    a reply. The list endpoint returns top-level comments with their reply tree
    nested, so a client gets a whole thread in one call.
    """

    queryset = Comment.objects.select_related(
        "document",
        "author",
        "parent",
    ).prefetch_related("replies__author")
    serializer_class = CommentSerializer

    def get_queryset(self):
        queryset = super().get_queryset()

        if self.action != "list":
            return queryset

        params = self.request.query_params

        document = params.get("document")
        if document:
            queryset = queryset.filter(document_id=document)

        author = params.get("author")
        if author:
            queryset = queryset.filter(author_id=author)

        parent = params.get("parent")
        if parent:
            queryset = queryset.filter(parent_id=parent)

        search = params.get("search")
        if search:
            queryset = queryset.filter(content__icontains=search)

        created_after = params.get("created_after")
        if created_after:
            queryset = queryset.filter(
                created_at__gte=parse_timestamp(created_after, "created_after")
            )

        created_before = params.get("created_before")
        if created_before:
            queryset = queryset.filter(
                created_at__lte=parse_timestamp(created_before, "created_before")
            )

        # Replies are nested inside their parent by default. Ask for the flat
        # list with ?include_replies=true.
        include_replies = params.get("include_replies", "").lower() == "true"
        if not include_replies and not parent:
            queryset = queryset.filter(parent__isnull=True)

        return queryset.order_by("created_at")

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            comment = serializer.save()

            AuditLog.objects.create(
                actor=comment.author,
                action="replied" if comment.parent_id else "commented",
                model_name="Comment",
                object_id=str(comment.pk),
            )

        return Response(
            self.get_serializer(comment).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["get"], url_path="thread")
    def thread(self, request, pk=None):
        """One comment plus its whole reply tree, walked up to the root first."""

        comment = self.get_object()

        root = comment
        while root.parent_id:
            root = root.parent

        return Response(
            {
                "requested": comment.id,
                "root": self.get_serializer(root).data,
            },
            status=status.HTTP_200_OK,
        )

    @action(detail=False, methods=["get"], url_path="summary")
    def summary(self, request):
        """Comment counts overall, per document and per author."""

        comments = Comment.objects.all()
        documents = Document.objects.all()

        workspace = request.query_params.get("workspace")
        if workspace:
            comments = comments.filter(document__workspace_id=workspace)
            documents = documents.filter(workspace_id=workspace)

        totals = comments.aggregate(
            total_comments=Count("id", distinct=True),
            top_level=Count("id", filter=Q(parent__isnull=True), distinct=True),
            replies=Count("id", filter=Q(parent__isnull=False), distinct=True),
        )

        per_document = list(
            documents.annotate(comment_total=Count("comments", distinct=True))
            .filter(comment_total__gt=0)
            .values("id", "title", "comment_total")
            .order_by("-comment_total")
        )

        per_author = list(
            comments.values("author__first_name", "author__last_name")
            .annotate(comment_total=Count("id"))
            .order_by("-comment_total")
        )

        uncommented_ids = list(
            documents.annotate(comment_total=Count("comments", distinct=True))
            .filter(comment_total=0)
            .values_list("id", flat=True)
        )

        return Response(
            {
                **totals,
                "per_document": per_document,
                "per_author": per_author,
                "documents_without_comments": uncommented_ids,
            },
            status=status.HTTP_200_OK,
        )
