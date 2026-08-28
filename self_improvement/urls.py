# -*- coding: utf-8 -*-
from django.urls import path
from . import views

urlpatterns = [
    path("tasks/",                views.TaskCreateView.as_view(),      name="si-tasks"),
    path("tasks/<uuid:task_id>/", views.TaskDetailView.as_view(),      name="si-task-detail"),
    path("improve/",              views.ImprovementCycleView.as_view(),name="si-improve"),
    path("stats/",                views.StatsView.as_view(),           name="si-stats"),
    path("diagnostics/",          views.DiagnosticsView.as_view(),     name="si-diagnostics"),
    path("autofix/",              views.AutoFixView.as_view(),         name="si-autofix"),
    path("monitor/",              views.MonitorView.as_view(),         name="si-monitor"),
    path("skills/learn/",         views.LearnSkillView.as_view(),      name="si-skills-learn"),
]
