from django.apps import AppConfig


class TyrepowerAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'tyrepower_app'

    def ready(self):
        import tyrepower_app.signals
