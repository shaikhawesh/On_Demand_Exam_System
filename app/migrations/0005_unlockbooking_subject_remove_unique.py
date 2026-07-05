"""Migration branch: add subject and remove unique_together (alternate branch).

This file was recreated to satisfy an existing merge migration that expects
two 0005 branches. It mirrors the other 0005 migration so the migration
graph is consistent.
"""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0004_remove_unlockslot_capacity'),
    ]

    operations = [
        migrations.AddField(
            model_name='unlockbooking',
            name='subject',
            field=models.CharField(max_length=150, null=True, blank=True),
        ),
        migrations.AlterUniqueTogether(
            name='unlockbooking',
            unique_together=set(),
        ),
        migrations.AlterModelOptions(
            name='unlockbooking',
            options={'ordering': ['-booked_at']},
        ),
    ]
