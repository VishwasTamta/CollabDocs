from datetime import datetime, time

from django.db import transaction
from django.db.models import Count, Q
from django.utils import timezone
from django.utils.dateparse import parse_date, parse_datetime
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from apps.auditlogs.models import AuditLog
from apps.tags.models import Tag
from apps.tags.serializers import AttachTagsSerializer, TagSerializer

from .models import Document, DocumentVersion
from .serializers import DocumentSerializer, DocumentVersionSerializer


def parse_timestamp(value, field_name):
    """Turn an ISO date or datetime query parameter into an aware datetime."""

    parsed = parse_datetime(value) or parse_date(value)

    if parsed is None:
        raise ValidationError(
            {
                field_name: (
                    "Expected an ISO date or datetime, "
                    "e.g. 2026-08-09 or 2026-08-09T10:30:00Z."
                )
            }
        )

    if not isinstance(parsed, datetime):
        parsed = datetime.combine(parsed, time.min)

    if timezone.is_naive(parsed):
        parsed = timezone.make_aware(parsed)

    return parsed


class DocumentViewSet(ModelViewSet):
    """
    Handles CRUD operations for Document, plus version history and stats.

    Every save - create or update - writes a new DocumentVersion inside the
    same transaction as the document itself.
    """

    queryset = Document.objects.select_related("workspace", "created_by").annotate(
        version_total=Count("versions", distinct=True)
    )
    serializer_class = DocumentSerializer

    def get_queryset(self):
        queryset = super().get_queryset()

        if self.action != "list":
            return queryset

        params = self.request.query_params

        workspace = params.get("workspace")
        if workspace:
            queryset = queryset.filter(workspace_id=workspace)

        created_by = params.get("created_by")
        if created_by:
            queryset = queryset.filter(created_by_id=created_by)

        document_status = params.get("status")
        if document_status:
            queryset = queryset.filter(status=document_status)

        status_in = params.get("status_in")
        if status_in:
            values = [item.strip() for item in status_in.split(",") if item.strip()]
            unknown = set(values) - set(Document.Status.values)
            if unknown:
                raise ValidationError(
                    {
                        "status_in": (
                            f"Unknown status value(s): {', '.join(sorted(unknown))}. "
                            f"Allowed: {', '.join(Document.Status.values)}."
                        )
                    }
                )
            queryset = queryset.filter(status__in=values)

        updated_after = params.get("updated_after")
        if updated_after:
            queryset = queryset.filter(
                updated_at__gte=parse_timestamp(updated_after, "updated_after")
            )

        updated_before = params.get("updated_before")
        if updated_before:
            queryset = queryset.filter(
                updated_at__lte=parse_timestamp(updated_before, "updated_before")
            )

        tag = params.get("tag")
        if tag:
            queryset = queryset.filter(tags__name__iexact=tag.strip().lower())

        tags_in = params.get("tags")
        if tags_in:
            values = [item.strip().lower() for item in tags_in.split(",") if item.strip()]
            queryset = queryset.filter(tags__name__in=values)

        # OR search across title and body.
        search = params.get("search")
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) | Q(content__icontains=search)
            )

        return queryset.distinct().order_by("-updated_at")

    def reload(self, document):
        """Re-read a document so annotated counts include the version just added."""

        return self.queryset.get(pk=document.pk)

    def create_version(self, document, saved_by):
        """Snapshot the current document body as the next version."""

        return DocumentVersion.objects.create(
            document=document,
            content=document.content,
            version_number=document.versions.count() + 1,
            saved_by=saved_by,
        )

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        saved_by = serializer.validated_data.pop("saved_by", None)

        # Document row, its first version and the AuditLog row written by the
        # post_save signal all live or die together.
        with transaction.atomic():
            document = serializer.save()
            self.create_version(document, saved_by or document.created_by)

        return Response(
            self.get_serializer(self.reload(document)).data,
            status=status.HTTP_201_CREATED,
        )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()

        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        saved_by = serializer.validated_data.pop("saved_by", None)

        with transaction.atomic():
            document = serializer.save()
            self.create_version(document, saved_by or document.created_by)

        return Response(self.get_serializer(self.reload(document)).data)

    @action(detail=True, methods=["get"], url_path="versions")
    def versions(self, request, pk=None):
        """Full version history for one document, oldest first."""

        document = self.get_object()

        versions = document.versions.select_related("saved_by").all()

        return Response(
            {
                "document": document.id,
                "title": document.title,
                "version_count": versions.count(),
                "versions": DocumentVersionSerializer(versions, many=True).data,
            },
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["post"], url_path="tags")
    def tags(self, request, pk=None):
        """
        Attach tags to a document, creating any name that does not exist yet.

        An M2M change fires no model post_save, so unlike a document save this
        action writes its own AuditLog row - inside the same atomic block as
        the tag attach, so the two cannot drift apart.
        """

        document = self.get_object()

        serializer = AttachTagsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        names = serializer.validated_data.get("tags", [])
        tag_ids = serializer.validated_data.get("tag_ids", [])
        actor = serializer.validated_data.get("actor") or document.created_by

        if tag_ids:
            found_ids = set(
                Tag.objects.filter(id__in=tag_ids).values_list("id", flat=True)
            )
            missing = [str(tag_id) for tag_id in tag_ids if tag_id not in found_ids]

            if missing:
                return Response(
                    {"detail": f"No tag found for id(s): {', '.join(missing)}."},
                    status=status.HTTP_404_NOT_FOUND,
                )

        with transaction.atomic():
            attached = [Tag.objects.get_or_create(name=name)[0] for name in names]

            if tag_ids:
                attached.extend(Tag.objects.filter(id__in=tag_ids))

            document.tags.add(*attached)

            AuditLog.objects.create(
                actor=actor,
                action="tagged",
                model_name="Document",
                object_id=str(document.pk),
            )

        return Response(
            {
                "document": document.id,
                "attached": TagSerializer(attached, many=True).data,
                "all_tags": list(document.tags.values_list("name", flat=True)),
            },
            status=status.HTTP_200_OK,
        )

    @action(detail=False, methods=["get"], url_path="stats")
    def stats(self, request):
        """Aggregated document counts, optionally scoped to one workspace."""

        documents = Document.objects.all()

        workspace = request.query_params.get("workspace")
        if workspace:
            documents = documents.filter(workspace_id=workspace)

        totals = documents.aggregate(
            total_documents=Count("id", distinct=True),
            total_versions=Count("versions", distinct=True),
            total_comments=Count("comments", distinct=True),
        )

        by_status = list(
            documents.values("status").annotate(count=Count("id")).order_by("status")
        )

        by_workspace = list(
            documents.values("workspace__name")
            .annotate(count=Count("id"))
            .order_by("-count")
        )

        draft_ids = list(
            documents.filter(status=Document.Status.DRAFT).values_list("id", flat=True)
        )

        return Response(
            {
                **totals,
                "by_status": by_status,
                "by_workspace": by_workspace,
                "draft_document_ids": draft_ids,
            },
            status=status.HTTP_200_OK,
        )
