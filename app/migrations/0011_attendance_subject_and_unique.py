from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0010_examresult'),
    ]

    operations = [
        migrations.AddField(
            model_name='attendance',
            name='subject',
            field=models.CharField(blank=True, default='', max_length=255),
        ),
        migrations.AlterUniqueTogether(
            name='attendance',
            unique_together={('user', 'slot', 'subject')},
        ),
    ]

