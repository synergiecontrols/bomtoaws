# Generated by Django 5.1 on 2025-01-06 11:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("bom_app", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="item",
            name="time_stamp",
            field=models.DateField(auto_now_add=True, default="2025-01-01"),
            preserve_default=False,
        ),
    ]