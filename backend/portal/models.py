"""
Models for the AtomQuest Goal Setting & Tracking Portal.
"""
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from datetime import datetime, timedelta


# ============================================================================
# Reference Data Models
# ============================================================================

class ThrustArea(models.Model):
    """Thrust Area reference model for goal categorization."""
    
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return self.name


class UoMType(models.Model):
    """Unit of Measure Type reference model."""
    
    TYPE_CHOICES = [
        ('numeric', 'Numeric'),
        ('percentage', 'Percentage'),
        ('timeline', 'Timeline'),
        ('zero_based', 'Zero-based'),
    ]
    
    name = models.CharField(max_length=50, choices=TYPE_CHOICES, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return self.get_name_display()


class Department(models.Model):
    """Department model for organizational structure."""
    
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return self.name


# ============================================================================
# User & Role Models
# ============================================================================

class UserProfile(models.Model):
    """Extended user profile with role and department information."""
    
    ROLE_CHOICES = [
        ('employee', 'Employee'),
        ('manager', 'Manager'),
        ('admin', 'Admin'),
        ('viewer', 'Viewer'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='employee')
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True, related_name='users')
    manager = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='subordinates')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['user__username']
        indexes = [
            models.Index(fields=['role']),
            models.Index(fields=['department']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return f"{self.user.username} ({self.get_role_display()})"


# ============================================================================
# Cycle Models
# ============================================================================

class Cycle(models.Model):
    """Performance cycle model."""
    
    STATUS_CHOICES = [
        ('planning', 'Planning'),
        ('active', 'Active'),
        ('closed', 'Closed'),
    ]
    
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='planning')
    
    start_date = models.DateField()
    end_date = models.DateField()
    
    # Check-in dates (quarterly)
    checkin_date_q1 = models.DateField(null=True, blank=True)  # July
    checkin_date_q2 = models.DateField(null=True, blank=True)  # October
    checkin_date_q3 = models.DateField(null=True, blank=True)  # January
    checkin_date_q4 = models.DateField(null=True, blank=True)  # March/April
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-start_date']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['start_date', 'end_date']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.get_status_display()})"
    
    def set_checkin_dates(self):
        """Automatically set quarterly check-in dates."""
        year = self.start_date.year
        self.checkin_date_q1 = datetime(year, 7, 15).date()  # July 15
        self.checkin_date_q2 = datetime(year, 10, 15).date()  # October 15
        self.checkin_date_q3 = datetime(year + 1, 1, 15).date()  # January 15
        self.checkin_date_q4 = datetime(year + 1, 4, 15).date()  # April 15


# ============================================================================
# Goal Models
# ============================================================================

class Goal(models.Model):
    """Goal model for performance objectives."""
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('locked', 'Locked'),
    ]
    
    # Basic information
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='goals')
    cycle = models.ForeignKey(Cycle, on_delete=models.CASCADE, related_name='goals')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, max_length=2000)
    
    # Classification
    thrust_area = models.ForeignKey(ThrustArea, on_delete=models.SET_NULL, null=True, blank=True, related_name='goals')
    uom_type = models.ForeignKey(UoMType, on_delete=models.SET_NULL, null=True, blank=True, related_name='goals')
    
    # Metrics
    target_value = models.FloatField(validators=[MinValueValidator(0)])
    weightage = models.FloatField(validators=[MinValueValidator(10), MaxValueValidator(100)])
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # Shared goal fields
    is_shared = models.BooleanField(default=False)
    shared_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='shared_goals_created')
    is_readonly_title = models.BooleanField(default=False)
    is_readonly_target = models.BooleanField(default=False)
    
    # Approval tracking
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='goals_approved')
    approved_at = models.DateTimeField(null=True, blank=True)
    approval_comments = models.TextField(blank=True, help_text="Comments provided during goal approval")
    rejection_reason = models.TextField(blank=True, help_text="Reason for goal rejection")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'cycle']),
            models.Index(fields=['user', 'status']),
            models.Index(fields=['cycle', 'status']),
            models.Index(fields=['is_shared']),
        ]
        unique_together = []  # Can have multiple goals per user per cycle
    
    def __str__(self):
        return f"{self.title} - {self.user.username}"
    
    def is_locked(self):
        """Check if goal is locked."""
        return self.status in ['approved', 'locked']
    
    def can_edit(self, user):
        """Check if user can edit this goal."""
        if user.profile.role == 'admin':
            return True
        if self.status == 'draft' and self.user == user:
            return True
        if self.status == 'submitted' and user.profile.role == 'manager':
            return True
        return False


class SharedGoal(models.Model):
    """Shared goal (KPI) model for departmental goals."""
    
    goal = models.OneToOneField(Goal, on_delete=models.CASCADE, related_name='shared_goal_info')
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='shared_goals')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='shared_goals_pushed')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['department']),
        ]
    
    def __str__(self):
        return f"Shared: {self.goal.title}"


# ============================================================================
# Check-in Models
# ============================================================================

class CheckIn(models.Model):
    """Check-in model for progress tracking."""
    
    STATUS_CHOICES = [
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    goal = models.ForeignKey(Goal, on_delete=models.CASCADE, related_name='checkins')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='checkins')
    cycle = models.ForeignKey(Cycle, on_delete=models.CASCADE, related_name='checkins')
    
    # Progress value
    progress_value = models.FloatField()
    progress_percentage = models.FloatField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    
    # Comments
    comments = models.TextField(blank=True)
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='submitted')
    
    # Approval tracking
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='checkins_approved')
    approved_at = models.DateTimeField(null=True, blank=True)
    rejection_comments = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['goal', 'cycle']),
            models.Index(fields=['user', 'cycle']),
            models.Index(fields=['status']),
        ]
        unique_together = [('goal', 'cycle')]  # One check-in per goal per cycle
    
    def __str__(self):
        return f"CheckIn: {self.goal.title} - {self.progress_percentage}%"


# ============================================================================
# Audit Trail Model
# ============================================================================

class AuditLog(models.Model):
    """Immutable audit trail for all system actions."""
    
    ENTITY_TYPES = [
        ('goal', 'Goal'),
        ('checkin', 'CheckIn'),
        ('user', 'User'),
        ('cycle', 'Cycle'),
    ]
    
    ACTIONS = [
        ('create', 'Create'),
        ('update', 'Update'),
        ('approve', 'Approve'),
        ('reject', 'Reject'),
        ('submit', 'Submit'),
        ('lock', 'Lock'),
        ('delete', 'Delete'),
    ]
    
    entity_type = models.CharField(max_length=50, choices=ENTITY_TYPES)
    entity_id = models.PositiveIntegerField()
    action = models.CharField(max_length=50, choices=ACTIONS)
    
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='audit_logs')
    
    old_values = models.JSONField(null=True, blank=True)
    new_values = models.JSONField(null=True, blank=True)
    
    comments = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['entity_type', 'entity_id']),
            models.Index(fields=['user']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.entity_type} - {self.action} - {self.created_at}"


# ============================================================================
# Notification Model
# ============================================================================

class Notification(models.Model):
    """Notification model for user notifications."""
    
    TYPE_CHOICES = [
        ('goal_submitted', 'Goal Submitted'),
        ('goal_approved', 'Goal Approved'),
        ('goal_rejected', 'Goal Rejected'),
        ('checkin_period_open', 'Check-in Period Open'),
        ('checkin_pending_review', 'Check-in Pending Review'),
        ('checkin_approved', 'Check-in Approved'),
        ('checkin_rejected', 'Check-in Rejected'),
        ('shared_goal_assigned', 'Shared Goal Assigned'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=255)
    message = models.TextField()
    notification_type = models.CharField(max_length=50, choices=TYPE_CHOICES)
    
    # Related objects
    goal = models.ForeignKey(Goal, on_delete=models.SET_NULL, null=True, blank=True, related_name='notifications')
    checkin = models.ForeignKey(CheckIn, on_delete=models.SET_NULL, null=True, blank=True, related_name='notifications')
    
    # Status
    is_read = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.user.username}"
