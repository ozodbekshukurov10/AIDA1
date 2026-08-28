# -*- coding: utf-8 -*-
"""
AIDA Self-Improvement System - Models
Task -> Execution -> Evaluation -> Strategy -> Knowledge
"""
from __future__ import annotations
import uuid
from django.db import models
from django.utils import timezone


class Task(models.Model):
    DOMAIN_CHOICES = [
        ("code","Kod"),("math","Matematika"),("language","Til"),
        ("reasoning","Mantiq"),("knowledge","Bilim"),("creative","Ijodiy"),
        ("analysis","Tahlil"),("general","Umumiy"),
    ]
    STATUS_CHOICES = [
        ("pending","Kutilmoqda"),("running","Bajarilmoqda"),
        ("done","Tugallandi"),("failed","Muvaffaqiyatsiz"),("retrying","Qayta"),
    ]
    id             = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_request   = models.TextField()
    goal           = models.TextField()
    constraints    = models.JSONField(default=list)
    expected_output= models.TextField(blank=True)
    difficulty     = models.IntegerField(default=1)
    domain         = models.CharField(max_length=50, choices=DOMAIN_CHOICES, default="general")
    status         = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    retry_count    = models.IntegerField(default=0)
    max_retries    = models.IntegerField(default=3)
    source         = models.CharField(max_length=50, default="user")
    created_at     = models.DateTimeField(auto_now_add=True)
    updated_at     = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "aida_tasks"
        ordering = ["-created_at"]

    def __str__(self):
        return f"[{self.domain}] {self.user_request[:80]}"

    def can_retry(self):
        return self.retry_count < self.max_retries


class Strategy(models.Model):
    id              = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name            = models.CharField(max_length=200, unique=True)
    description     = models.TextField(blank=True)
    prompt_template = models.TextField()
    domain          = models.CharField(max_length=50, default="general")
    conditions      = models.JSONField(default=dict)
    success_rate    = models.FloatField(default=0.5)
    usage_count     = models.IntegerField(default=0)
    is_active       = models.BooleanField(default=True)
    created_at      = models.DateTimeField(auto_now_add=True)
    updated_at      = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "aida_strategies"
        ordering = ["-success_rate"]

    def __str__(self):
        return f"{self.name} ({self.success_rate:.0%})"

    def update_success_rate(self, was_successful):
        alpha = 0.1
        score = 1.0 if was_successful else 0.0
        self.success_rate = (1 - alpha) * self.success_rate + alpha * score
        self.usage_count += 1
        self.save(update_fields=["success_rate", "usage_count", "updated_at"])


class Execution(models.Model):
    id             = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    task           = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="executions")
    strategy       = models.ForeignKey(Strategy, on_delete=models.SET_NULL, null=True, blank=True)
    attempt_number = models.IntegerField(default=1)
    model_used     = models.CharField(max_length=100, default="gemini")
    prompt_sent    = models.TextField()
    output         = models.TextField(blank=True)
    time_taken_ms  = models.IntegerField(default=0)
    token_count    = models.IntegerField(default=0)
    is_successful  = models.BooleanField(default=False)
    error_message  = models.TextField(blank=True)
    created_at     = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "aida_executions"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Exec #{self.attempt_number} for Task {self.task_id}"


class Evaluation(models.Model):
    ERROR_TYPES = [
        ("none","Xato yoq"),("logic","Mantiqiy"),("factual","Faktik"),
        ("format","Format"),("incomplete","Tolik emas"),
        ("irrelevant","Mavzudan tashqari"),("hallucination","Noto'g'ri"),
    ]
    id              = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    execution       = models.OneToOneField(Execution, on_delete=models.CASCADE, related_name="evaluation")
    score           = models.FloatField(default=0.0)
    relevance_score = models.FloatField(default=0.0)
    clarity_score   = models.FloatField(default=0.0)
    accuracy_score  = models.FloatField(default=0.0)
    error_detected  = models.BooleanField(default=False)
    error_type      = models.CharField(max_length=30, choices=ERROR_TYPES, default="none")
    feedback        = models.TextField(blank=True)
    improved        = models.BooleanField(default=False)
    evaluator       = models.CharField(max_length=50, default="auto")
    created_at      = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "aida_evaluations"
        ordering = ["-created_at"]

    def is_good(self):
        return self.score >= 0.75


class KnowledgeChunk(models.Model):
    id              = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    domain          = models.CharField(max_length=50, default="general")
    title           = models.CharField(max_length=300)
    content         = models.TextField()
    source          = models.CharField(max_length=100, default="execution")
    tags            = models.JSONField(default=list)
    relevance_score = models.FloatField(default=1.0)
    used_count      = models.IntegerField(default=0)
    last_used       = models.DateTimeField(null=True, blank=True)
    is_verified     = models.BooleanField(default=False)
    created_at      = models.DateTimeField(auto_now_add=True)
    updated_at      = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "aida_knowledge"
        ordering = ["-relevance_score", "-used_count"]

    def __str__(self):
        return f"[{self.domain}] {self.title[:80]}"

    def mark_used(self):
        self.used_count += 1
        self.last_used = timezone.now()
        self.save(update_fields=["used_count", "last_used"])


class ImprovementLog(models.Model):
    id                 = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cycle_number       = models.IntegerField(default=1)
    trigger            = models.CharField(max_length=100, default="scheduler")
    tasks_analyzed     = models.IntegerField(default=0)
    strategies_updated = models.IntegerField(default=0)
    knowledge_added    = models.IntegerField(default=0)
    avg_score_before   = models.FloatField(default=0.0)
    avg_score_after    = models.FloatField(default=0.0)
    summary            = models.TextField(blank=True)
    created_at         = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "aida_improvement_logs"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Cycle #{self.cycle_number} â€” {self.created_at}"
