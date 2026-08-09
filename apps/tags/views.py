from django.db import IntegrityError, transaction
from django.db.models import Count
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from apps.documents.serializers import DocumentSerializer

from .models import Tag
from .serializers import TagSerializer


class TagViewSet(ModelViewSet):
    """
    Handles CRUD operations for Tag.

    Tag names are unique, so a duplicate create is reported as 409 rather than
    letting the IntegrityError surface as a 500.
    """

    queryset = Tag.objects.annotate(document_total=Count("documents", distinct=True))
    serializer_class = TagSerializer

    def get_queryset(self):
        queryset = super().get_queryset()

        if self.action != "list":
            return queryset

        params = self.request.query_params

        search = params.get("search")
        if search:
            queryset = queryset.filter(name__icontains=search)

        names = params.get("names")
        if names:
            values = [item.strip().lower() for item in names.split(",") if item.strip()]
            queryset = queryset.filter(name__in=values)

        return queryset.order_by("name")

    def name_conflict(self, serializer):
        return Response(
            {
                "detail": (
                    f"A tag named '{serializer.validated_data['name']}' "
                    "already exists."
                )
            },
            status=status.HTTP_409_CONFLICT,
        )

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            with transaction.atomic():
                tag = serializer.save()
        except IntegrityError:
            return self.name_conflict(serializer)

        return Response(
            self.get_serializer(tag).data,
            status=status.HTTP_201_CREATED,
        )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()

        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        try:
            with transaction.atomic():
                tag = serializer.save()
        except IntegrityError:
            return self.name_conflict(serializer)

        return Response(self.get_serializer(tag).data)

    @action(detail=True, methods=["get"], url_path="documents")
    def documents(self, request, pk=None):
        """Every document carrying this tag."""

        tag = self.get_object()

        documents = tag.documents.select_related("workspace", "created_by").annotate(
            version_total=Count("versions", distinct=True)
        )

        return Response(
            {
                "tag": tag.name,
                "document_count": documents.count(),
                "documents": DocumentSerializer(documents, many=True).data,
            },
            status=status.HTTP_200_OK,
        )
