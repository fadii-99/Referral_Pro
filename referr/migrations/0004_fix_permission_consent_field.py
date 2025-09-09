# Generated manually to fix MariaDB compatibility issue

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('referr', '0003_referral_reference_id'),
    ]

    operations = [
        # Add the new field with the correct name
        migrations.AddField(
            model_name='referral',
            name='permission_consent',
            field=models.BooleanField(default=False),
        ),
        # Copy data from old field to new field using RunSQL
        migrations.RunSQL(
            "UPDATE referr_referral SET permission_consent = permission_concent;",
            reverse_sql="UPDATE referr_referral SET permission_concent = permission_consent;",
        ),
        # Remove the old field
        migrations.RemoveField(
            model_name='referral',
            name='permission_concent',
        ),
    ]
