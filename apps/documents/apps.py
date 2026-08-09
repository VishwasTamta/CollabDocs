from django.apps import AppConfig


class DocumentsConfig(AppConfig):
    name = 'apps.documents'

    def ready(self):
        from . import signals  # noqa: F401
