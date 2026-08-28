from django.apps import AppConfig

class SelfImprovementConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "self_improvement"
    verbose_name = "AIDA Self-Improvement"

    def ready(self):
        pass
