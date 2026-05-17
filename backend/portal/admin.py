"""
Django admin configuration for AtomQuest Goal Setting & Tracking Portal.
"""
from django.contrib import admin
from .models import (
    UserProfile, Department, ThrustArea, UoMType, Cycle,
    Goal, SharedGoal, CheckIn, AuditLog, Notification
)


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name',)


@admin.register(ThrustArea)
class ThrustAreaAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name',)


@admin.register(UoMType)
class UoMTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name',)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'department', 'manager', 'is_active', 'created_at')
    list_filter = ('role', 'department', 'is_active', 'created_at')
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Cycle)
class CycleAdmin(admin.ModelAdmin):
    list_display = ('name', 'status', 'start_date', 'end_date', 'created_at')
    list_filter = ('status', 'start_date', 'created_at')
    search_fields = ('name',)
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Goal)
class GoalAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'cycle', 'status', 'weightage', 'is_shared', 'created_at')
    list_filter = ('status', 'cycle', 'is_shared', 'created_at')
    search_fields = ('title', 'user__username')
    readonly_fields = ('created_at', 'updated_at', 'approved_at')


@admin.register(SharedGoal)
class SharedGoalAdmin(admin.ModelAdmin):
    list_display = ('goal', 'department', 'created_by', 'created_at')
    list_filter = ('department', 'created_at')
    search_fields = ('goal__title', 'department__name')
    readonly_fields = ('created_at',)


@admin.register(CheckIn)
class CheckInAdmin(admin.ModelAdmin):
    list_display = ('goal', 'user', 'cycle', 'status', 'progress_percentage', 'created_at')
    list_filter = ('status', 'cycle', 'created_at')
    search_fields = ('goal__title', 'user__username')
    readonly_fields = ('created_at', 'updated_at', 'approved_at')


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('entity_type', 'entity_id', 'action', 'user', 'created_at')
    list_filter = ('entity_type', 'action', 'created_at')
    search_fields = ('user__username',)
    readonly_fields = ('created_at', 'entity_type', 'entity_id', 'action', 'user', 'old_values', 'new_values', 'comments', 'ip_address', 'user_agent')


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'notification_type', 'is_read', 'created_at')
    list_filter = ('notification_type', 'is_read', 'created_at')
    search_fields = ('title', 'user__username')
    readonly_fields = ('created_at', 'read_at')
