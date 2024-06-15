# Generated by Django 4.2.13 on 2024-06-08 09:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("django_oscar_es", "0001_initial"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="productfacet",
            options={"ordering": ["order"]},
        ),
        migrations.AddField(
            model_name="productfacet",
            name="order",
            field=models.PositiveIntegerField(
                default=0,
                help_text="The order in which this facet should be displayed.",
            ),
        ),
    ]