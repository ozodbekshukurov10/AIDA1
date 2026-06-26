from django.db import models
from django.utils import timezone


class AccessKey(models.Model):
    name = models.CharField(max_length=120)
    prefix = models.CharField(max_length=24, unique=True)
    key_hash = models.CharField(max_length=64, unique=True)
    platform_name = models.CharField(max_length=120, blank=True)
    business_type = models.CharField(max_length=80, blank=True)
    audience = models.CharField(max_length=120, blank=True)
    tone = models.CharField(max_length=80, blank=True)
    assistant_goal = models.CharField(max_length=160, blank=True)
    custom_instructions = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_used_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        app_label = "webapp"
        ordering = ["-created_at"]

    def mark_used(self) -> None:
        self.last_used_at = timezone.now()
        self.save(update_fields=["last_used_at"])

    def __str__(self) -> str:
        return f"{self.name} ({self.prefix})"

    def profile_summary(self) -> str:
        parts = [
            self.platform_name.strip(),
            self.business_type.strip(),
            self.audience.strip(),
            self.tone.strip(),
            self.assistant_goal.strip(),
        ]
        return " | ".join(part for part in parts if part)
