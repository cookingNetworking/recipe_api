# Generated by Django 3.2.23 on 2023-11-15 14:09

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0013_alter_recipecomment_photo'),
    ]

    operations = [
        migrations.AddField(
            model_name='recipe',
            name='comment',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='recipe_of_comment', to='core.recipecomment'),
        ),
    ]
