# Generated by Django 3.2.23 on 2023-11-21 07:48

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0017_alter_recipecomment_recipe'),
    ]

    operations = [
        migrations.RenameField(
            model_name='recipecomment',
            old_name='crated_time',
            new_name='created_time',
        ),
    ]
