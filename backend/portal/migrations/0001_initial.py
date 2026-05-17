# Generated migration for AtomQuest models

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.core.validators


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # Create ThrustArea
        migrations.CreateModel(
            name='ThrustArea',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, unique=True)),
                ('description', models.TextField(blank=True)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'ordering': ['name'],
            },
        ),
        
        # Create UoMType
        migrations.CreateModel(
            name='UoMType',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(choices=[('numeric', 'Numeric'), ('percentage', 'Percentage'), ('timeline', 'Timeline'), ('zero_based', 'Zero-based')], max_length=50, unique=True)),
                ('description', models.TextField(blank=True)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'ordering': ['name'],
            },
        ),
        
        # Create Department
        migrations.CreateModel(
            name='Department',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, unique=True)),
                ('description', models.TextField(blank=True)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'ordering': ['name'],
            },
        ),
        
        # Create Cycle
        migrations.CreateModel(
            name='Cycle',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('description', models.TextField(blank=True)),
                ('status', models.CharField(choices=[('planning', 'Planning'), ('active', 'Active'), ('closed', 'Closed')], default='planning', max_length=20)),
                ('start_date', models.DateField()),
                ('end_date', models.DateField()),
                ('checkin_date_q1', models.DateField(blank=True, null=True)),
                ('checkin_date_q2', models.DateField(blank=True, null=True)),
                ('checkin_date_q3', models.DateField(blank=True, null=True)),
                ('checkin_date_q4', models.DateField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'ordering': ['-start_date'],
            },
        ),
        
        # Create UserProfile
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('role', models.CharField(choices=[('employee', 'Employee'), ('manager', 'Manager'), ('admin', 'Admin')], default='employee', max_length=20)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('department', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='users', to='portal.department')),
                ('manager', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='subordinates', to=settings.AUTH_USER_MODEL)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='profile', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['user__username'],
            },
        ),
        
        # Create Goal
        migrations.CreateModel(
            name='Goal',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255)),
                ('description', models.TextField(blank=True, max_length=2000)),
                ('target_value', models.FloatField(validators=[django.core.validators.MinValueValidator(0)])),
                ('weightage', models.FloatField(validators=[django.core.validators.MinValueValidator(10), django.core.validators.MaxValueValidator(100)])),
                ('status', models.CharField(choices=[('draft', 'Draft'), ('submitted', 'Submitted'), ('approved', 'Approved'), ('rejected', 'Rejected'), ('locked', 'Locked')], default='draft', max_length=20)),
                ('is_shared', models.BooleanField(default=False)),
                ('is_readonly_title', models.BooleanField(default=False)),
                ('is_readonly_target', models.BooleanField(default=False)),
                ('approved_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('approved_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='goals_approved', to=settings.AUTH_USER_MODEL)),
                ('cycle', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='goals', to='portal.cycle')),
                ('shared_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='shared_goals_created', to=settings.AUTH_USER_MODEL)),
                ('thrust_area', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='goals', to='portal.thrustarea')),
                ('uom_type', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='goals', to='portal.uomtype')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='goals', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        
        # Create SharedGoal
        migrations.CreateModel(
            name='SharedGoal',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='shared_goals_pushed', to=settings.AUTH_USER_MODEL)),
                ('department', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='shared_goals', to='portal.department')),
                ('goal', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='shared_goal_info', to='portal.goal')),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        
        # Create CheckIn
        migrations.CreateModel(
            name='CheckIn',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('progress_value', models.FloatField()),
                ('progress_percentage', models.FloatField(default=0, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(100)])),
                ('comments', models.TextField(blank=True)),
                ('status', models.CharField(choices=[('submitted', 'Submitted'), ('approved', 'Approved'), ('rejected', 'Rejected')], default='submitted', max_length=20)),
                ('approved_at', models.DateTimeField(blank=True, null=True)),
                ('rejection_comments', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('approved_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='checkins_approved', to=settings.AUTH_USER_MODEL)),
                ('cycle', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='checkins', to='portal.cycle')),
                ('goal', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='checkins', to='portal.goal')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='checkins', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created_at'],
                'unique_together': {('goal', 'cycle')},
            },
        ),
        
        # Create AuditLog
        migrations.CreateModel(
            name='AuditLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('entity_type', models.CharField(choices=[('goal', 'Goal'), ('checkin', 'CheckIn'), ('user', 'User'), ('cycle', 'Cycle')], max_length=50)),
                ('entity_id', models.PositiveIntegerField()),
                ('action', models.CharField(choices=[('create', 'Create'), ('update', 'Update'), ('approve', 'Approve'), ('reject', 'Reject'), ('submit', 'Submit'), ('lock', 'Lock'), ('delete', 'Delete')], max_length=50)),
                ('old_values', models.JSONField(blank=True, null=True)),
                ('new_values', models.JSONField(blank=True, null=True)),
                ('comments', models.TextField(blank=True)),
                ('ip_address', models.GenericIPAddressField(blank=True, null=True)),
                ('user_agent', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='audit_logs', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        
        # Create Notification
        migrations.CreateModel(
            name='Notification',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255)),
                ('message', models.TextField()),
                ('notification_type', models.CharField(choices=[('goal_submitted', 'Goal Submitted'), ('goal_approved', 'Goal Approved'), ('goal_rejected', 'Goal Rejected'), ('checkin_period_open', 'Check-in Period Open'), ('checkin_pending_review', 'Check-in Pending Review'), ('checkin_approved', 'Check-in Approved'), ('checkin_rejected', 'Check-in Rejected'), ('shared_goal_assigned', 'Shared Goal Assigned')], max_length=50)),
                ('is_read', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('read_at', models.DateTimeField(blank=True, null=True)),
                ('checkin', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='notifications', to='portal.checkin')),
                ('goal', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='notifications', to='portal.goal')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='notifications', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        
        # Add indexes
        migrations.AddIndex(
            model_name='thrustarea',
            index=models.Index(fields=['is_active'], name='portal_thru_is_acti_idx'),
        ),
        migrations.AddIndex(
            model_name='uomtype',
            index=models.Index(fields=['is_active'], name='portal_uomt_is_acti_idx'),
        ),
        migrations.AddIndex(
            model_name='department',
            index=models.Index(fields=['is_active'], name='portal_depa_is_acti_idx'),
        ),
        migrations.AddIndex(
            model_name='cycle',
            index=models.Index(fields=['status'], name='portal_cycl_status_idx'),
        ),
        migrations.AddIndex(
            model_name='cycle',
            index=models.Index(fields=['start_date', 'end_date'], name='portal_cycl_start_d_idx'),
        ),
        migrations.AddIndex(
            model_name='userprofile',
            index=models.Index(fields=['role'], name='portal_user_role_idx'),
        ),
        migrations.AddIndex(
            model_name='userprofile',
            index=models.Index(fields=['department'], name='portal_user_depart_idx'),
        ),
        migrations.AddIndex(
            model_name='userprofile',
            index=models.Index(fields=['is_active'], name='portal_user_is_acti_idx'),
        ),
        migrations.AddIndex(
            model_name='goal',
            index=models.Index(fields=['user', 'cycle'], name='portal_goal_user_cy_idx'),
        ),
        migrations.AddIndex(
            model_name='goal',
            index=models.Index(fields=['user', 'status'], name='portal_goal_user_st_idx'),
        ),
        migrations.AddIndex(
            model_name='goal',
            index=models.Index(fields=['cycle', 'status'], name='portal_goal_cycle_s_idx'),
        ),
        migrations.AddIndex(
            model_name='goal',
            index=models.Index(fields=['is_shared'], name='portal_goal_is_shar_idx'),
        ),
        migrations.AddIndex(
            model_name='sharedgoal',
            index=models.Index(fields=['department'], name='portal_shar_depart_idx'),
        ),
        migrations.AddIndex(
            model_name='checkin',
            index=models.Index(fields=['goal', 'cycle'], name='portal_chec_goal_cy_idx'),
        ),
        migrations.AddIndex(
            model_name='checkin',
            index=models.Index(fields=['user', 'cycle'], name='portal_chec_user_cy_idx'),
        ),
        migrations.AddIndex(
            model_name='checkin',
            index=models.Index(fields=['status'], name='portal_chec_status_idx'),
        ),
        migrations.AddIndex(
            model_name='auditlog',
            index=models.Index(fields=['entity_type', 'entity_id'], name='portal_audi_entity__idx'),
        ),
        migrations.AddIndex(
            model_name='auditlog',
            index=models.Index(fields=['user'], name='portal_audi_user_id_idx'),
        ),
        migrations.AddIndex(
            model_name='auditlog',
            index=models.Index(fields=['created_at'], name='portal_audi_created_idx'),
        ),
        migrations.AddIndex(
            model_name='notification',
            index=models.Index(fields=['user', 'is_read'], name='portal_noti_user_is_idx'),
        ),
        migrations.AddIndex(
            model_name='notification',
            index=models.Index(fields=['created_at'], name='portal_noti_created_idx'),
        ),
    ]
