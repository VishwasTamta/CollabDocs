import uuid

from django.db import models

from apps.documents.models import Document


class Tag(models.Model):

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    name = models.CharField(
        max_length=100,
        unique=True
    )
    documents = models.ManyToManyField(
        Document,
        related_name="tags",
        blank=True
    )

    class Meta:
        verbose_name = "Tag"
        verbose_name_plural = "Tags"
        db_table = "tags"

    def __str__(self):
        return self.name