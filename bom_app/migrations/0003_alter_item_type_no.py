# Generated by Django 5.1 on 2025-01-06 11:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("bom_app", "0002_item_time_stamp"),
    ]

    operations = [
        migrations.AlterField(
            model_name="item",
            name="type_no",
            field=models.CharField(max_length=100, unique=True),
        ),
    ]
