from django.apps import AppConfig


class AidaApiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'aida_api'
    verbose_name = 'AIDA Enterprise API'
    label = 'aida_api'

    def ready(self):
        pass
