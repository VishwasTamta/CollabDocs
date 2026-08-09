from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.auditlogs.models import AuditLog

from .models import Document


@receiver(post_save, sender=Document, dispatch_uid="document_audit_log")
def log_document_save(sender, instance, created, **kwargs):
    """
    Record every document save in the audit trail.

    The views save documents inside a transaction.atomic() block, so this
    AuditLog row is written in the same transaction as the document and the
    DocumentVersion - if any of them fails, none of them is kept.

    Note: instance._state.adding is already False by the time post_save runs,
    so the `created` flag the signal hands us is the reliable source. It is
    kept below only as a fallback for direct saves that bypass the signal's
    created flag.
    """

    is_create = created or instance._state.adding

    AuditLog.objects.create(
        actor=instance.created_by,
        action="created" if is_create else "updated",
        model_name="Document",
        object_id=str(instance.pk),
    )
