# Empty no-op migration created to keep migration graph stable.
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0006_merge_20251113_2153'),
    ]

    operations = [
        # Intentionally empty: this migration is a no-op to preserve a stable
        # migration graph after manual edits. It avoids reversing previously
        # applied schema changes.
    ]
