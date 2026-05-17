# Generated migration for adding approval comments and rejection reason fields

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('portal', '0003_add_viewer_role'),
    ]

    operations = [
        migrations.AddField(
            model_name='goal',
            name='approval_comments',
            field=models.TextField(blank=True, help_text='Comments provided during goal approval'),
        ),
        migrations.AddField(
            model_name='goal',
            name='rejection_reason',
            field=models.TextField(blank=True, help_text='Reason for goal rejection'),
        ),
    ]
