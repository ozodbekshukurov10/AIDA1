from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("webapp", "0001_accesskey"),
    ]

    operations = [
        migrations.AddField(
            model_name="accesskey",
            name="assistant_goal",
            field=models.CharField(blank=True, max_length=160),
        ),
        migrations.AddField(
            model_name="accesskey",
            name="audience",
            field=models.CharField(blank=True, max_length=120),
        ),
        migrations.AddField(
            model_name="accesskey",
            name="business_type",
            field=models.CharField(blank=True, max_length=80),
        ),
        migrations.AddField(
            model_name="accesskey",
            name="custom_instructions",
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name="accesskey",
            name="platform_name",
            field=models.CharField(blank=True, max_length=120),
        ),
        migrations.AddField(
            model_name="accesskey",
            name="tone",
            field=models.CharField(blank=True, max_length=80),
        ),
    ]
