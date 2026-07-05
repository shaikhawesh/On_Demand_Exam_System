from django.apps import AppConfig


class AppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'app'

    def ready(self) -> None:
        # Ensures signal receivers are registered
        from . import models  # noqa: F401
        return super().ready()