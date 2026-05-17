# Generated migration to add Viewer role to UserProfile

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('portal', '0002_seed_reference_data'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userprofile',
            name='role',
            field=models.CharField(
                choices=[
                    ('employee', 'Employee'),
                    ('manager', 'Manager'),
                    ('admin', 'Admin'),
                    ('viewer', 'Viewer'),
                ],
                default='employee',
                max_length=20
            ),
        ),
    ]
