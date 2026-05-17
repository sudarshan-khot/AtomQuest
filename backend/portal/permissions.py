"""
Permission classes for the AtomQuest Goal Setting & Tracking Portal.
Implements comprehensive role-based access control (RBAC) with 4 roles:
Admin, Manager, Employee, and Viewer.
"""
from rest_framework import permissions
from rest_framework.exceptions import PermissionDenied
from django.db.models import Q


# ============================================================================
# Role-Based Permission Classes
# ============================================================================

class IsEmployee(permissions.BasePermission):
    """Permission class for employee-only access."""
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and \
               hasattr(request.user, 'profile') and \
               request.user.profile.role == 'employee'


class IsManager(permissions.BasePermission):
    """Permission class for manager-only access."""
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and \
               hasattr(request.user, 'profile') and \
               request.user.profile.role == 'manager'


class IsAdmin(permissions.BasePermission):
    """Permission class for admin-only access."""
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and \
               hasattr(request.user, 'profile') and \
               request.user.profile.role == 'admin'


class IsViewer(permissions.BasePermission):
    """Permission class for viewer-only access (read-only)."""
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and \
               hasattr(request.user, 'profile') and \
               request.user.profile.role == 'viewer'


class IsManagerOrAdmin(permissions.BasePermission):
    """Permission class for manager and admin access."""
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and \
               hasattr(request.user, 'profile') and \
               request.user.profile.role in ['manager', 'admin']


class IsEmployeeOrManager(permissions.BasePermission):
    """Permission class for employee and manager access."""
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and \
               hasattr(request.user, 'profile') and \
               request.user.profile.role in ['employee', 'manager']


class IsAuthenticatedUser(permissions.BasePermission):
    """Permission class for authenticated users."""
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated


# ============================================================================
# Object-Level Permission Classes
# ============================================================================

class IsGoalOwnerOrManager(permissions.BasePermission):
    """
    Permission class for goal access.
    Allows:
    - Goal owner (employee) to access their own goals
    - Manager to access their team's goals
    - Admin to access all goals
    """
    
    def has_object_permission(self, request, view, obj):
        user = request.user
        if not hasattr(user, 'profile'):
            return False
        
        # Admin can access all goals
        if user.profile.role == 'admin':
            return True
        
        # Goal owner can access their own goals
        if obj.user == user:
            return True
        
        # Manager can access their team's goals
        if user.profile.role == 'manager':
            return obj.user.profile.manager == user
        
        return False


class IsCheckInOwnerOrManager(permissions.BasePermission):
    """
    Permission class for check-in access.
    Allows:
    - Check-in owner (employee) to access their own check-ins
    - Manager to access their team's check-ins
    - Admin to access all check-ins
    """
    
    def has_object_permission(self, request, view, obj):
        user = request.user
        if not hasattr(user, 'profile'):
            return False
        
        # Admin can access all check-ins
        if user.profile.role == 'admin':
            return True
        
        # Check-in owner can access their own check-ins
        if obj.user == user:
            return True
        
        # Manager can access their team's check-ins
        if user.profile.role == 'manager':
            return obj.user.profile.manager == user
        
        return False


class CanApproveGoal(permissions.BasePermission):
    """
    Permission class for goal approval.
    Only managers and admins can approve goals.
    """
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and \
               hasattr(request.user, 'profile') and \
               request.user.profile.role in ['manager', 'admin']
    
    def has_object_permission(self, request, view, obj):
        user = request.user
        if not hasattr(user, 'profile'):
            return False
        
        # Admin can approve any goal
        if user.profile.role == 'admin':
            return True
        
        # Manager can approve their team's goals
        if user.profile.role == 'manager':
            return obj.user.profile.manager == user
        
        return False


class CanApproveCheckIn(permissions.BasePermission):
    """
    Permission class for check-in approval.
    Only managers and admins can approve check-ins.
    """
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and \
               hasattr(request.user, 'profile') and \
               request.user.profile.role in ['manager', 'admin']
    
    def has_object_permission(self, request, view, obj):
        user = request.user
        if not hasattr(user, 'profile'):
            return False
        
        # Admin can approve any check-in
        if user.profile.role == 'admin':
            return True
        
        # Manager can approve their team's check-ins
        if user.profile.role == 'manager':
            return obj.user.profile.manager == user
        
        return False


class IsReadOnly(permissions.BasePermission):
    """Permission class for read-only access."""
    
    def has_permission(self, request, view):
        return request.method in permissions.SAFE_METHODS


class CanManageUsers(permissions.BasePermission):
    """Permission class for user management (admin only)."""
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and \
               hasattr(request.user, 'profile') and \
               request.user.profile.role == 'admin'


class CanManageCycles(permissions.BasePermission):
    """Permission class for cycle management (admin only)."""
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and \
               hasattr(request.user, 'profile') and \
               request.user.profile.role == 'admin'


class CanManageReferenceData(permissions.BasePermission):
    """Permission class for reference data management (admin only)."""
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and \
               hasattr(request.user, 'profile') and \
               request.user.profile.role == 'admin'


# ============================================================================
# Permission Utility Functions
# ============================================================================

def check_role_permission(user, required_role):
    """
    Check if user has the required role.
    
    Args:
        user: Django User object
        required_role: String or list of required roles
    
    Returns:
        Boolean indicating if user has permission
    
    Raises:
        PermissionDenied: If user doesn't have required role
    """
    if not user or not user.is_authenticated:
        raise PermissionDenied("User is not authenticated")
    
    if not hasattr(user, 'profile'):
        raise PermissionDenied("User profile not found")
    
    if isinstance(required_role, str):
        required_role = [required_role]
    
    if user.profile.role not in required_role:
        raise PermissionDenied(f"Insufficient permissions. Required role: {required_role}")
    
    return True


def check_object_permission(user, obj, permission_type='view'):
    """
    Check if user has permission to access an object.
    
    Args:
        user: Django User object
        obj: Object to check permission for (Goal, CheckIn, etc.)
        permission_type: Type of permission ('view', 'edit', 'approve', 'delete')
    
    Returns:
        Boolean indicating if user has permission
    
    Raises:
        PermissionDenied: If user doesn't have permission
    """
    if not user or not user.is_authenticated:
        raise PermissionDenied("User is not authenticated")
    
    if not hasattr(user, 'profile'):
        raise PermissionDenied("User profile not found")
    
    # Admin can do anything
    if user.profile.role == 'admin':
        return True
    
    # Determine object type and check permission
    obj_type = type(obj).__name__
    
    if obj_type == 'Goal':
        if permission_type == 'view':
            # Owner or manager can view
            if obj.user == user or obj.user.profile.manager == user:
                return True
        elif permission_type == 'edit':
            # Only owner can edit (if not locked)
            if obj.user == user and not obj.is_locked():
                return True
        elif permission_type == 'approve':
            # Only manager can approve
            if user.profile.role == 'manager' and obj.user.profile.manager == user:
                return True
    
    elif obj_type == 'CheckIn':
        if permission_type == 'view':
            # Owner or manager can view
            if obj.user == user or obj.user.profile.manager == user:
                return True
        elif permission_type == 'edit':
            # Only owner can edit (if not approved)
            if obj.user == user and obj.status != 'approved':
                return True
        elif permission_type == 'approve':
            # Only manager can approve
            if user.profile.role == 'manager' and obj.user.profile.manager == user:
                return True
    
    raise PermissionDenied(f"Insufficient permissions for {permission_type} on {obj_type}")


def get_filtered_queryset(user, queryset, model_type='goal'):
    """
    Filter queryset based on user role and permissions.
    
    Args:
        user: Django User object
        queryset: Django QuerySet to filter
        model_type: Type of model ('goal', 'checkin', 'user', 'audit')
    
    Returns:
        Filtered QuerySet
    """
    if not user or not user.is_authenticated:
        return queryset.none()
    
    if not hasattr(user, 'profile'):
        return queryset.none()
    
    # Admin can see everything
    if user.profile.role == 'admin':
        return queryset
    
    # Viewer can see everything (read-only)
    if user.profile.role == 'viewer':
        return queryset
    
    # Manager can see their team's data
    if user.profile.role == 'manager':
        if model_type == 'goal':
            return queryset.filter(
                Q(user=user) | Q(user__profile__manager=user)
            )
        elif model_type == 'checkin':
            return queryset.filter(
                Q(user=user) | Q(user__profile__manager=user)
            )
        elif model_type == 'user':
            return queryset.filter(
                Q(user=user) | Q(manager=user)
            )
        elif model_type == 'audit':
            return queryset.filter(
                Q(user=user) | Q(user__profile__manager=user)
            )
    
    # Employee can only see their own data
    if user.profile.role == 'employee':
        if model_type == 'goal':
            return queryset.filter(user=user)
        elif model_type == 'checkin':
            return queryset.filter(user=user)
        elif model_type == 'user':
            return queryset.filter(user=user)
        elif model_type == 'audit':
            return queryset.filter(user=user)
    
    return queryset.none()
