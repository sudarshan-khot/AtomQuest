"""
Serializers for the AtomQuest Goal Setting & Tracking Portal.
"""
from rest_framework import serializers
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError as DjangoValidationError
from .models import (
    UserProfile, Department, ThrustArea, UoMType, Cycle,
    Goal, SharedGoal, CheckIn, AuditLog, Notification
)
from .validators import (
    GoalFieldValidator, GoalWeightageValidator, GoalCountValidator,
    CheckInValidator, SharedGoalValidator, CycleStatusValidator
)


# ============================================================================
# Reference Data Serializers
# ============================================================================

class ThrustAreaSerializer(serializers.ModelSerializer):
    class Meta:
        model = ThrustArea
        fields = ['id', 'name', 'description', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class UoMTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = UoMType
        fields = ['id', 'name', 'description', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = ['id', 'name', 'description', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


# ============================================================================
# User & Role Serializers
# ============================================================================

class UserBasicSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']
        read_only_fields = ['id']


class UserProfileSerializer(serializers.ModelSerializer):
    user = UserBasicSerializer(read_only=True)
    department_name = serializers.CharField(source='department.name', read_only=True)
    manager_name = serializers.CharField(source='manager.username', read_only=True, allow_null=True)
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    
    class Meta:
        model = UserProfile
        fields = [
            'id', 'user', 'role', 'role_display', 'department', 'department_name',
            'manager', 'manager_name', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']


class UserDetailSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer(read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'profile']
        read_only_fields = ['id']


class UserCreateSerializer(serializers.Serializer):
    """Serializer for creating new users with role assignment."""
    username = serializers.CharField(max_length=150, required=True)
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True, required=True, min_length=8)
    first_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    last_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    role = serializers.ChoiceField(choices=['employee', 'manager', 'admin', 'viewer'], default='employee')
    department_id = serializers.IntegerField(required=False, allow_null=True)
    manager_id = serializers.IntegerField(required=False, allow_null=True)
    
    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Username already exists.")
        return value
    
    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already exists.")
        return value
    
    def validate_password(self, value):
        if len(value) < 8:
            raise serializers.ValidationError("Password must be at least 8 characters long.")
        return value


class UserUpdateRoleSerializer(serializers.Serializer):
    """Serializer for updating user role and manager assignment.
    user_id comes from the URL pk, not the request body.
    """
    role = serializers.ChoiceField(choices=['employee', 'manager', 'admin', 'viewer'], required=False)
    manager_id = serializers.IntegerField(required=False, allow_null=True)
    department_id = serializers.IntegerField(required=False, allow_null=True)


# ============================================================================
# Cycle Serializers
# ============================================================================

class CycleSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Cycle
        fields = [
            'id', 'name', 'description', 'status', 'status_display',
            'start_date', 'end_date',
            'checkin_date_q1', 'checkin_date_q2', 'checkin_date_q3', 'checkin_date_q4',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


# ============================================================================
# Goal Serializers
# ============================================================================

class GoalSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.username', read_only=True)
    thrust_area_name = serializers.CharField(source='thrust_area.name', read_only=True, allow_null=True)
    uom_type_name = serializers.CharField(source='uom_type.get_name_display', read_only=True, allow_null=True)
    approved_by_name = serializers.CharField(source='approved_by.username', read_only=True, allow_null=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Goal
        fields = [
            'id', 'user', 'user_name', 'cycle', 'title', 'description',
            'thrust_area', 'thrust_area_name', 'uom_type', 'uom_type_name',
            'target_value', 'weightage', 'status', 'status_display',
            'is_shared', 'shared_by', 'is_readonly_title', 'is_readonly_target',
            'approved_by', 'approved_by_name', 'approved_at', 'approval_comments',
            'rejection_reason', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'approved_by', 'approved_at', 'approval_comments', 'rejection_reason', 'created_at', 'updated_at']


class GoalCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Goal
        fields = [
            'title', 'description', 'cycle', 'thrust_area', 'uom_type',
            'target_value', 'weightage'
        ]
    
    def validate_title(self, value):
        """Validate goal title using GoalFieldValidator."""
        try:
            GoalFieldValidator.validate_title(value)
        except DjangoValidationError as e:
            raise serializers.ValidationError(str(e))
        return value
    
    def validate_description(self, value):
        """Validate goal description using GoalFieldValidator."""
        try:
            GoalFieldValidator.validate_description(value)
        except DjangoValidationError as e:
            raise serializers.ValidationError(str(e))
        return value
    
    def validate_target_value(self, value):
        """Validate target value using GoalFieldValidator."""
        try:
            GoalFieldValidator.validate_target_value(value)
        except DjangoValidationError as e:
            raise serializers.ValidationError(str(e))
        return value
    
    def validate_weightage(self, value):
        """Validate weightage using GoalWeightageValidator."""
        try:
            GoalWeightageValidator.validate_individual_weightage(value)
        except DjangoValidationError as e:
            raise serializers.ValidationError(str(e))
        return value


class SharedGoalSerializer(serializers.ModelSerializer):
    goal = GoalSerializer(read_only=True)
    department_name = serializers.CharField(source='department.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True, allow_null=True)
    
    class Meta:
        model = SharedGoal
        fields = [
            'id', 'goal', 'department', 'department_name',
            'created_by', 'created_by_name', 'created_at'
        ]
        read_only_fields = ['id', 'goal', 'created_by', 'created_at']


# ============================================================================
# Check-in Serializers
# ============================================================================

class CheckInSerializer(serializers.ModelSerializer):
    goal_title = serializers.CharField(source='goal.title', read_only=True)
    user_name = serializers.CharField(source='user.username', read_only=True)
    approved_by_name = serializers.CharField(source='approved_by.username', read_only=True, allow_null=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = CheckIn
        fields = [
            'id', 'goal', 'goal_title', 'user', 'user_name', 'cycle',
            'progress_value', 'progress_percentage', 'comments',
            'status', 'status_display',
            'approved_by', 'approved_by_name', 'approved_at', 'rejection_comments',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'user', 'progress_percentage', 'approved_by', 'approved_at',
            'created_at', 'updated_at'
        ]


class CheckInCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CheckIn
        fields = ['goal', 'cycle', 'progress_value', 'comments']
    
    def validate_progress_value(self, value):
        """Validate progress value is non-negative."""
        if value < 0:
            raise serializers.ValidationError("Progress value cannot be negative.")
        return value
    
    def validate(self, data):
        """Validate complete check-in data."""
        goal = data.get('goal')
        cycle = data.get('cycle')
        progress_value = data.get('progress_value')
        
        if goal and cycle and progress_value is not None:
            try:
                CheckInValidator.validate_checkin_submission(goal, cycle, progress_value)
            except DjangoValidationError as e:
                raise serializers.ValidationError(str(e))
        
        return data



# ============================================================================
# Audit Trail Serializers
# ============================================================================

class AuditLogSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.username', read_only=True, allow_null=True)
    entity_type_display = serializers.CharField(source='get_entity_type_display', read_only=True)
    action_display = serializers.CharField(source='get_action_display', read_only=True)
    
    class Meta:
        model = AuditLog
        fields = [
            'id', 'entity_type', 'entity_type_display', 'entity_id',
            'action', 'action_display', 'user', 'user_name',
            'old_values', 'new_values', 'comments',
            'ip_address', 'user_agent', 'created_at'
        ]
        read_only_fields = [
            'id', 'entity_type', 'entity_id', 'action', 'user',
            'old_values', 'new_values', 'ip_address', 'user_agent', 'created_at'
        ]


# ============================================================================
# Notification Serializers
# ============================================================================

class NotificationSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.username', read_only=True)
    goal_title = serializers.CharField(source='goal.title', read_only=True, allow_null=True)
    type_display = serializers.CharField(source='get_notification_type_display', read_only=True)
    
    class Meta:
        model = Notification
        fields = [
            'id', 'user', 'user_name', 'title', 'message', 'notification_type', 'type_display',
            'goal', 'goal_title', 'checkin', 'is_read', 'created_at', 'read_at'
        ]
        read_only_fields = ['id', 'user', 'created_at']
