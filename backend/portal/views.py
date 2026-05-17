"""
Views for the AtomQuest Goal Setting & Tracking Portal.
"""
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied, ValidationError
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db.models import Q, Sum
from django.utils import timezone
from datetime import datetime, timedelta

from .models import (
    UserProfile, Department, ThrustArea, UoMType, Cycle,
    Goal, SharedGoal, CheckIn, AuditLog, Notification
)
from .serializers import (
    UserProfileSerializer, UserDetailSerializer, DepartmentSerializer,
    ThrustAreaSerializer, UoMTypeSerializer, CycleSerializer,
    GoalSerializer, GoalCreateUpdateSerializer, SharedGoalSerializer,
    CheckInSerializer, CheckInCreateUpdateSerializer,
    AuditLogSerializer, NotificationSerializer,
    UserCreateSerializer, UserUpdateRoleSerializer
)
from .permissions import (
    IsEmployee, IsManager, IsAdmin, IsViewer, IsManagerOrAdmin,
    IsEmployeeOrManager, IsAuthenticatedUser, IsGoalOwnerOrManager,
    IsCheckInOwnerOrManager, CanApproveGoal, CanApproveCheckIn,
    CanManageUsers, CanManageCycles, CanManageReferenceData,
    get_filtered_queryset, check_role_permission, check_object_permission
)
from .utils import (
    log_audit_trail, calculate_progress_percentage, get_client_ip,
    send_notification, validate_weightage
)


# ============================================================================
# Permission Classes
# ============================================================================

class IsAdminUser(permissions.BasePermission):
    """Permission class for admin-only access."""
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and \
               hasattr(request.user, 'profile') and \
               request.user.profile.role == 'admin'


class IsManagerOrAdmin(permissions.BasePermission):
    """Permission class for manager and admin access."""
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and \
               hasattr(request.user, 'profile') and \
               request.user.profile.role in ['manager', 'admin']


class IsAuthenticatedUser(permissions.BasePermission):
    """Permission class for authenticated users."""
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated


# ============================================================================
# Reference Data ViewSets
# ============================================================================

class ThrustAreaViewSet(viewsets.ModelViewSet):
    """ViewSet for Thrust Area management."""
    
    queryset = ThrustArea.objects.filter(is_active=True)
    serializer_class = ThrustAreaSerializer
    permission_classes = [IsAuthenticatedUser]
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdminUser()]
        return [IsAuthenticatedUser()]


class UoMTypeViewSet(viewsets.ModelViewSet):
    """ViewSet for UoM Type management."""
    
    queryset = UoMType.objects.filter(is_active=True)
    serializer_class = UoMTypeSerializer
    permission_classes = [IsAuthenticatedUser]
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdminUser()]
        return [IsAuthenticatedUser()]


class DepartmentViewSet(viewsets.ModelViewSet):
    """ViewSet for Department management."""
    
    queryset = Department.objects.filter(is_active=True)
    serializer_class = DepartmentSerializer
    permission_classes = [IsAuthenticatedUser]
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdminUser()]
        return [IsAuthenticatedUser()]


# ============================================================================
# User Management ViewSets (Phase 2)
# ============================================================================

class UserProfileViewSet(viewsets.ModelViewSet):
    """ViewSet for User Profile management."""
    
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticatedUser]
    
    def get_queryset(self):
        user = self.request.user
        if not hasattr(user, 'profile'):
            return UserProfile.objects.none()
        
        if user.profile.role == 'admin':
            return UserProfile.objects.all()
        elif user.profile.role == 'manager':
            # Managers can see their subordinates
            return UserProfile.objects.filter(manager=user)
        else:
            # Employees can only see themselves
            return UserProfile.objects.filter(user=user)
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy', 'list']:
            return [IsAdminUser()]
        return [IsAuthenticatedUser()]
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        """Get current user's profile."""
        try:
            profile = request.user.profile
            serializer = self.get_serializer(profile)
            return Response(serializer.data)
        except UserProfile.DoesNotExist:
            return Response(
                {'error': 'User profile not found'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=False, methods=['get'])
    def team(self, request):
        """Get team members for a manager."""
        user = request.user
        if not hasattr(user, 'profile') or user.profile.role not in ['manager', 'admin']:
            raise PermissionDenied("Only managers and admins can view team members.")
        
        if user.profile.role == 'admin':
            team_members = UserProfile.objects.all()
        else:
            team_members = UserProfile.objects.filter(manager=user)
        
        serializer = self.get_serializer(team_members, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        """Deactivate a user."""
        if not request.user.profile.role == 'admin':
            raise PermissionDenied("Only admins can deactivate users.")
        
        profile = self.get_object()
        profile.is_active = False
        profile.save()
        
        # Log audit trail
        log_audit_trail(
            entity_type='user',
            entity_id=profile.user.id,
            action='update',
            user=request.user,
            old_values={'is_active': True},
            new_values={'is_active': False},
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        serializer = self.get_serializer(profile)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def reactivate(self, request, pk=None):
        """Reactivate a user."""
        if not request.user.profile.role == 'admin':
            raise PermissionDenied("Only admins can reactivate users.")
        
        profile = self.get_object()
        profile.is_active = True
        profile.save()
        
        # Log audit trail
        log_audit_trail(
            entity_type='user',
            entity_id=profile.user.id,
            action='update',
            user=request.user,
            old_values={'is_active': False},
            new_values={'is_active': True},
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        serializer = self.get_serializer(profile)
        return Response(serializer.data)


class UserManagementViewSet(viewsets.ViewSet):
    """ViewSet for user management operations (Admin only)."""
    
    permission_classes = [IsAdminUser]
    
    def list(self, request):
        """List all users with their roles and departments."""
        users = User.objects.all()
        serializer = UserDetailSerializer(users, many=True)
        return Response(serializer.data)
    
    def create(self, request):
        """Create a new user with role assignment."""
        serializer = UserCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        username = serializer.validated_data['username']
        email = serializer.validated_data['email']
        password = serializer.validated_data['password']
        role = serializer.validated_data.get('role', 'employee')
        department_id = serializer.validated_data.get('department_id')
        manager_id = serializer.validated_data.get('manager_id')
        first_name = serializer.validated_data.get('first_name', '')
        last_name = serializer.validated_data.get('last_name', '')
        
        # Create user
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name
        )
        
        # Create user profile
        department = None
        if department_id:
            try:
                department = Department.objects.get(id=department_id)
            except Department.DoesNotExist:
                user.delete()
                return Response(
                    {'error': 'Department not found'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        manager = None
        if manager_id:
            try:
                manager = User.objects.get(id=manager_id)
            except User.DoesNotExist:
                user.delete()
                return Response(
                    {'error': 'Manager not found'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        profile = UserProfile.objects.create(
            user=user,
            role=role,
            department=department,
            manager=manager
        )
        
        # Log audit trail
        log_audit_trail(
            entity_type='user',
            entity_id=user.id,
            action='create',
            user=request.user,
            new_values={
                'username': username,
                'email': email,
                'role': role,
                'department_id': department_id,
                'manager_id': manager_id
            },
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        result_serializer = UserDetailSerializer(user)
        return Response(result_serializer.data, status=status.HTTP_201_CREATED)
    
    def retrieve(self, request, pk=None):
        """Retrieve a specific user."""
        try:
            user = User.objects.get(id=pk)
            serializer = UserDetailSerializer(user)
            return Response(serializer.data)
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    def update(self, request, pk=None):
        """Update user role and manager assignment."""
        try:
            user = User.objects.get(id=pk)
            profile = user.profile
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = UserUpdateRoleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        old_values = {
            'role': profile.role,
            'manager_id': profile.manager_id,
            'department_id': profile.department_id
        }
        
        # Update role if provided
        if 'role' in serializer.validated_data:
            profile.role = serializer.validated_data['role']
        
        # Update manager if provided
        if 'manager_id' in serializer.validated_data:
            manager_id = serializer.validated_data['manager_id']
            if manager_id:
                try:
                    manager = User.objects.get(id=manager_id)
                    profile.manager = manager
                except User.DoesNotExist:
                    return Response(
                        {'error': 'Manager not found'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            else:
                profile.manager = None
        
        # Update department if provided
        if 'department_id' in serializer.validated_data:
            department_id = serializer.validated_data['department_id']
            if department_id:
                try:
                    department = Department.objects.get(id=department_id)
                    profile.department = department
                except Department.DoesNotExist:
                    return Response(
                        {'error': 'Department not found'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            else:
                profile.department = None
        
        profile.save()
        
        new_values = {
            'role': profile.role,
            'manager_id': profile.manager_id,
            'department_id': profile.department_id
        }
        
        # Log audit trail
        log_audit_trail(
            entity_type='user',
            entity_id=user.id,
            action='update',
            user=request.user,
            old_values=old_values,
            new_values=new_values,
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        result_serializer = UserDetailSerializer(user)
        return Response(result_serializer.data)
    
    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        """Deactivate a user."""
        try:
            user = User.objects.get(id=pk)
            profile = user.profile
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        if not profile.is_active:
            return Response(
                {'error': 'User is already deactivated'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        profile.is_active = False
        profile.save()
        
        # Log audit trail
        log_audit_trail(
            entity_type='user',
            entity_id=user.id,
            action='update',
            user=request.user,
            old_values={'is_active': True},
            new_values={'is_active': False},
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        serializer = UserDetailSerializer(user)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def reactivate(self, request, pk=None):
        """Reactivate a user."""
        try:
            user = User.objects.get(id=pk)
            profile = user.profile
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        if profile.is_active:
            return Response(
                {'error': 'User is already active'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        profile.is_active = True
        profile.save()
        
        # Log audit trail
        log_audit_trail(
            entity_type='user',
            entity_id=user.id,
            action='update',
            user=request.user,
            old_values={'is_active': False},
            new_values={'is_active': True},
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        serializer = UserDetailSerializer(user)
        return Response(serializer.data)


# ============================================================================
# Cycle Management ViewSet
# ============================================================================

class CycleViewSet(viewsets.ModelViewSet):
    """ViewSet for Cycle management.
    
    Read access: all authenticated users (needed for goal creation dropdown).
    Write access: admin only.
    """

    queryset = Cycle.objects.all()
    serializer_class = CycleSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [IsAuthenticatedUser()]
        return [IsAdminUser()]
    
    def create(self, request, *args, **kwargs):
        """Create a new cycle with automatic check-in dates."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        cycle = serializer.save()
        cycle.set_checkin_dates()
        cycle.save()
        
        # Log audit trail
        log_audit_trail(
            entity_type='cycle',
            entity_id=cycle.id,
            action='create',
            user=request.user,
            new_values={
                'name': cycle.name,
                'start_date': str(cycle.start_date),
                'end_date': str(cycle.end_date)
            },
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        return Response(self.get_serializer(cycle).data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """Activate a cycle (Planning -> Active)."""
        cycle = self.get_object()
        
        if cycle.status != 'planning':
            return Response(
                {'error': 'Only cycles in Planning status can be activated'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        cycle.status = 'active'
        cycle.save()
        
        # Log audit trail
        log_audit_trail(
            entity_type='cycle',
            entity_id=cycle.id,
            action='update',
            user=request.user,
            old_values={'status': 'planning'},
            new_values={'status': 'active'},
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        serializer = self.get_serializer(cycle)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def close(self, request, pk=None):
        """Close a cycle (Active -> Closed)."""
        cycle = self.get_object()
        
        if cycle.status != 'active':
            return Response(
                {'error': 'Only active cycles can be closed'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        cycle.status = 'closed'
        cycle.save()
        
        # Log audit trail
        log_audit_trail(
            entity_type='cycle',
            entity_id=cycle.id,
            action='update',
            user=request.user,
            old_values={'status': 'active'},
            new_values={'status': 'closed'},
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        serializer = self.get_serializer(cycle)
        return Response(serializer.data)


# ============================================================================
# Goal Management ViewSets
# ============================================================================

class GoalViewSet(viewsets.ModelViewSet):
    """ViewSet for Goal management."""
    
    queryset = Goal.objects.all()
    serializer_class = GoalSerializer
    permission_classes = [IsAuthenticatedUser]
    
    def get_queryset(self):
        user = self.request.user
        if not hasattr(user, 'profile'):
            return Goal.objects.none()

        role = user.profile.role
        if role == 'admin':
            return Goal.objects.all()
        elif role == 'manager':
            # Own goals + direct reports' goals
            return Goal.objects.filter(
                Q(user=user) | Q(user__profile__manager=user)
            )
        elif role == 'viewer':
            # Read-only access to all goals
            return Goal.objects.all()
        else:
            # Employee — own goals only
            return Goal.objects.filter(user=user)
    
    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return GoalCreateUpdateSerializer
        return GoalSerializer
    
    def create(self, request, *args, **kwargs):
        """Create a new goal."""
        from .validators import CycleStatusValidator, GoalCountValidator

        user = request.user

        # Viewers cannot create goals
        if hasattr(user, 'profile') and user.profile.role == 'viewer':
            raise PermissionDenied("Viewers cannot create goals.")

        cycle_id = request.data.get('cycle')
        
        # Get cycle
        try:
            cycle = Cycle.objects.get(id=cycle_id)
        except Cycle.DoesNotExist:
            return Response(
                {'error': 'Cycle not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check cycle status - CONSTRAINT: Goals can only be created during active cycles
        try:
            CycleStatusValidator.validate_cycle_active_for_goals(cycle)
        except (ValidationError, DjangoValidationError) as e:
            msg = e.message if isinstance(e, DjangoValidationError) and hasattr(e, 'message') else str(e)
            return Response({'error': msg}, status=status.HTTP_400_BAD_REQUEST)
        
        # Check goal count
        try:
            GoalCountValidator.validate_goal_count(user, cycle)
        except (ValidationError, DjangoValidationError) as e:
            msg = e.message if isinstance(e, DjangoValidationError) and hasattr(e, 'message') else str(e)
            return Response({'error': msg}, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        goal = serializer.save(user=user)
        
        # Log audit trail
        log_audit_trail(
            entity_type='goal',
            entity_id=goal.id,
            action='create',
            user=request.user,
            new_values={
                'title': goal.title,
                'target_value': goal.target_value,
                'weightage': goal.weightage,
                'status': goal.status
            },
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        return Response(GoalSerializer(goal).data, status=status.HTTP_201_CREATED)
    
    def update(self, request, *args, **kwargs):
        """Update a goal."""
        from .validators import CycleStatusValidator
        
        goal = self.get_object()
        user = request.user
        
        # Check permissions
        if not goal.can_edit(user):
            raise PermissionDenied("You do not have permission to edit this goal.")
        
        # CONSTRAINT: Goals cannot be edited after cycle closure
        try:
            CycleStatusValidator.validate_goal_not_edited_after_cycle_closure(goal, goal.cycle)
        except (ValidationError, DjangoValidationError) as e:
            msg = e.message if isinstance(e, DjangoValidationError) and hasattr(e, 'message') else str(e)
            return Response({'error': msg}, status=status.HTTP_400_BAD_REQUEST)
        
        # Check readonly fields for shared goals
        if goal.is_shared:
            if 'title' in request.data and request.data['title'] != goal.title:
                return Response(
                    {'error': 'Shared goal fields are read-only'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            if 'target_value' in request.data and request.data['target_value'] != goal.target_value:
                return Response(
                    {'error': 'Shared goal fields are read-only'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        serializer = self.get_serializer(goal, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        
        old_values = {
            'title': goal.title,
            'target_value': goal.target_value,
            'weightage': goal.weightage
        }
        
        goal = serializer.save()
        
        new_values = {
            'title': goal.title,
            'target_value': goal.target_value,
            'weightage': goal.weightage
        }
        
        # Log audit trail
        log_audit_trail(
            entity_type='goal',
            entity_id=goal.id,
            action='update',
            user=request.user,
            old_values=old_values,
            new_values=new_values,
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        return Response(GoalSerializer(goal).data)
    
    @action(detail=True, methods=['post'])
    def submit(self, request, pk=None):
        """Submit a goal for approval."""
        goal = self.get_object()
        
        if goal.user != request.user and request.user.profile.role != 'admin':
            raise PermissionDenied("You can only submit your own goals.")
        
        if goal.status != 'draft':
            return Response(
                {'error': 'Only draft goals can be submitted'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate weightage
        cycle_goals = Goal.objects.filter(user=goal.user, cycle=goal.cycle).exclude(id=goal.id)
        total_weightage = sum(g.weightage for g in cycle_goals) + goal.weightage
        
        if total_weightage != 100:
            return Response(
                {'error': f'Total weightage must be exactly 100%. Current: {total_weightage}%'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        goal.status = 'submitted'
        goal.save()
        
        # Log audit trail
        log_audit_trail(
            entity_type='goal',
            entity_id=goal.id,
            action='submit',
            user=request.user,
            new_values={'status': 'submitted'},
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        # Send notification to manager
        if goal.user.profile.manager:
            send_notification(
                user=goal.user.profile.manager,
                title='Goal Submitted for Approval',
                message=f'{goal.user.username} submitted goal "{goal.title}" for approval',
                notification_type='goal_submitted',
                goal=goal
            )
        
        return Response(GoalSerializer(goal).data)
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve a goal with optional approval comments."""
        goal = self.get_object()
        user = request.user
        approval_comments = request.data.get('approval_comments', '')
        
        if not hasattr(user, 'profile') or user.profile.role not in ['manager', 'admin']:
            raise PermissionDenied("Only managers and admins can approve goals.")
        
        if goal.status != 'submitted':
            return Response(
                {'error': 'Only submitted goals can be approved'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        goal.status = 'approved'
        goal.approved_by = user
        goal.approved_at = timezone.now()
        goal.approval_comments = approval_comments
        goal.save()
        
        # Log audit trail
        log_audit_trail(
            entity_type='goal',
            entity_id=goal.id,
            action='approve',
            user=request.user,
            old_values={'status': 'submitted'},
            new_values={
                'status': 'approved',
                'approved_by': user.username,
                'approved_at': str(goal.approved_at),
                'approval_comments': approval_comments
            },
            comments=approval_comments,
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        # Send notification to employee
        send_notification(
            user=goal.user,
            title='Goal Approved',
            message=f'Your goal "{goal.title}" has been approved' + (f'. Comments: {approval_comments}' if approval_comments else ''),
            notification_type='goal_approved',
            goal=goal
        )
        
        return Response(GoalSerializer(goal).data)
    
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Reject a goal with rejection reason."""
        goal = self.get_object()
        user = request.user
        rejection_reason = request.data.get('rejection_reason', '')
        
        if not hasattr(user, 'profile') or user.profile.role not in ['manager', 'admin']:
            raise PermissionDenied("Only managers and admins can reject goals.")
        
        if goal.status != 'submitted':
            return Response(
                {'error': 'Only submitted goals can be rejected'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not rejection_reason:
            return Response(
                {'error': 'Rejection reason is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        goal.status = 'rejected'
        goal.rejection_reason = rejection_reason
        goal.save()
        
        # Log audit trail
        log_audit_trail(
            entity_type='goal',
            entity_id=goal.id,
            action='reject',
            user=request.user,
            old_values={'status': 'submitted'},
            new_values={
                'status': 'rejected',
                'rejection_reason': rejection_reason
            },
            comments=rejection_reason,
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        # Send notification to employee
        send_notification(
            user=goal.user,
            title='Goal Rejected',
            message=f'Your goal "{goal.title}" has been rejected. Reason: {rejection_reason}',
            notification_type='goal_rejected',
            goal=goal
        )
        
        return Response(GoalSerializer(goal).data)
    
    @action(detail=True, methods=['patch'])
    def edit_during_review(self, request, pk=None):
        """
        Allow managers to edit goals during approval review.
        
        This endpoint enables inline editing of goal fields while the goal is in
        'submitted' status. Only managers and admins can use this endpoint.
        
        Editable fields during review:
        - title
        - description
        - target_value
        - weightage
        - thrust_area
        - uom_type
        
        Readonly fields (cannot be edited):
        - Shared goal title and target (if is_shared=True)
        
        All edits are logged in the audit trail with old and new values.
        """
        goal = self.get_object()
        user = request.user
        
        # Check permissions
        if not hasattr(user, 'profile') or user.profile.role not in ['manager', 'admin']:
            raise PermissionDenied("Only managers and admins can edit goals during review.")
        
        # Check goal status - must be submitted for inline editing
        if goal.status != 'submitted':
            return Response(
                {'error': 'Inline editing is only allowed for goals in submitted status'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate shared goal readonly fields
        if goal.is_shared:
            if 'title' in request.data and request.data['title'] != goal.title:
                return Response(
                    {'error': 'Shared goal title is read-only and cannot be edited'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            if 'target_value' in request.data and float(request.data['target_value']) != float(goal.target_value):
                return Response(
                    {'error': 'Shared goal target value is read-only and cannot be edited'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Capture old values for audit trail
        old_values = {
            'title': goal.title,
            'description': goal.description,
            'target_value': float(goal.target_value),
            'weightage': float(goal.weightage),
            'thrust_area_id': goal.thrust_area_id,
            'uom_type_id': goal.uom_type_id,
        }
        
        # Use the serializer to validate and update
        serializer = self.get_serializer(goal, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        
        # Save the updated goal
        goal = serializer.save()
        
        # Capture new values for audit trail
        new_values = {
            'title': goal.title,
            'description': goal.description,
            'target_value': float(goal.target_value),
            'weightage': float(goal.weightage),
            'thrust_area_id': goal.thrust_area_id,
            'uom_type_id': goal.uom_type_id,
        }
        
        # Log audit trail with detailed change information
        log_audit_trail(
            entity_type='goal',
            entity_id=goal.id,
            action='update',
            user=request.user,
            old_values=old_values,
            new_values=new_values,
            comments=f'Inline edit during approval review by {user.username}',
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        # Send notification to employee about the edit
        send_notification(
            user=goal.user,
            title='Goal Updated During Review',
            message=f'Your goal "{goal.title}" has been updated by your manager during the approval review',
            notification_type='goal_submitted',
            goal=goal
        )
        
        return Response(GoalSerializer(goal).data)
    
    @action(detail=False, methods=['get'])
    def pending(self, request):
        """
        Get all pending (submitted) goals for manager review.
        
        Managers see submitted goals from their direct reports.
        Admins see all submitted goals.
        """
        user = request.user
        
        if not hasattr(user, 'profile') or user.profile.role not in ['manager', 'admin']:
            raise PermissionDenied("Only managers and admins can view pending goals.")
        
        if user.profile.role == 'admin':
            pending_goals = Goal.objects.filter(status='submitted')
        else:
            # Managers see submitted goals from their direct reports
            pending_goals = Goal.objects.filter(
                status='submitted',
                user__profile__manager=user
            )
        
        serializer = GoalSerializer(pending_goals, many=True)
        return Response(serializer.data)


# ============================================================================
# Check-in Management ViewSet
# ============================================================================

class CheckInViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Check-in management.

    Endpoints:
      GET  /api/checkins/approved_goals/   - List approved goals available for check-in (Task 19)
      POST /api/checkins/                  - Create a draft check-in for a goal (Task 19)
      POST /api/checkins/{id}/submit/      - Submit a draft check-in with progress value (Task 19)
      GET  /api/checkins/pending/          - List pending check-ins for manager review (Task 21)
      POST /api/checkins/{id}/approve/     - Approve a check-in (Task 21)
      POST /api/checkins/{id}/reject/      - Reject a check-in with comments (Task 21)
    """

    queryset = CheckIn.objects.all()
    serializer_class = CheckInSerializer
    permission_classes = [IsAuthenticatedUser]

    def get_queryset(self):
        user = self.request.user
        if not hasattr(user, 'profile'):
            return CheckIn.objects.none()

        role = user.profile.role
        if role == 'admin':
            return CheckIn.objects.all()
        elif role == 'manager':
            return CheckIn.objects.filter(
                Q(user=user) | Q(user__profile__manager=user)
            )
        elif role == 'viewer':
            return CheckIn.objects.all()
        else:
            # Employee — own check-ins only
            return CheckIn.objects.filter(user=user)

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return CheckInCreateUpdateSerializer
        return CheckInSerializer

    # ------------------------------------------------------------------
    # Task 19: GET /api/checkins/approved_goals/
    # ------------------------------------------------------------------

    @action(detail=False, methods=['get'])
    def approved_goals(self, request):
        """
        Return approved goals for the current user that are eligible for check-in.

        A goal is eligible when:
        - It belongs to the requesting user
        - Its status is 'approved'
        - The goal's cycle is active

        Requirements: 8.1, 8.2
        """
        user = request.user

        # Employees see their own approved goals; managers/admins also see their own
        approved_goals = Goal.objects.filter(
            user=user,
            status='approved',
            cycle__status='active',
        ).select_related('cycle', 'thrust_area', 'uom_type')

        serializer = GoalSerializer(approved_goals, many=True)
        return Response(serializer.data)

    # ------------------------------------------------------------------
    # Task 19: POST /api/checkins/  (create a draft check-in)
    # ------------------------------------------------------------------

    def create(self, request, *args, **kwargs):
        """
        Create a new check-in record for an approved goal.

        Validates:
        - Cycle exists and is active
        - Goal exists and is approved
        - Progress value is valid for the goal's UoM type
        - Quarterly check-in period is active (±7 days window)

        Calculates progress percentage using the scoring engine.
        Logs the creation to the audit trail.

        Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 8.6, 8.7, 8.8, 13.1–13.6
        """
        from .validators import CycleStatusValidator, CheckInValidator

        user = request.user
        cycle_id = request.data.get('cycle')
        goal_id = request.data.get('goal')

        # Resolve cycle
        try:
            cycle = Cycle.objects.get(id=cycle_id)
        except Cycle.DoesNotExist:
            return Response({'error': 'Cycle not found'}, status=status.HTTP_404_NOT_FOUND)

        # Cycle must be active
        try:
            CycleStatusValidator.validate_cycle_active_for_checkins(cycle)
        except (ValidationError, DjangoValidationError) as e:
            msg = e.message if isinstance(e, DjangoValidationError) and hasattr(e, 'message') else str(e)
            return Response({'error': msg}, status=status.HTTP_400_BAD_REQUEST)

        # Resolve goal
        try:
            goal = Goal.objects.get(id=goal_id)
        except Goal.DoesNotExist:
            return Response({'error': 'Goal not found'}, status=status.HTTP_404_NOT_FOUND)

        # Goal must belong to the requesting user
        if goal.user != user and user.profile.role not in ['manager', 'admin']:
            raise PermissionDenied("You can only create check-ins for your own goals.")

        # Goal must be approved
        if goal.status != 'approved':
            return Response(
                {'error': f'Goal must be approved before submitting check-in. Current status: {goal.get_status_display()}'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Validate quarterly check-in period (±7 days window) — Task 20
        try:
            CheckInValidator.validate_checkin_period(cycle)
        except (ValidationError, DjangoValidationError) as e:
            msg = e.message if isinstance(e, DjangoValidationError) and hasattr(e, 'message') else str(e)
            # Include next check-in date in the response for UI display
            from .utils import validate_checkin_period as util_validate_period
            _, next_date, _ = util_validate_period(cycle)
            return Response(
                {
                    'error': msg,
                    'next_checkin_date': str(next_date) if next_date else None,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Validate progress value against UoM constraints
        progress_value = request.data.get('progress_value')
        if progress_value is not None:
            try:
                CheckInValidator.validate_progress_value(goal, progress_value)
            except (ValidationError, DjangoValidationError) as e:
                msg = e.message if isinstance(e, DjangoValidationError) and hasattr(e, 'message') else str(e)
                return Response({'error': msg}, status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Calculate progress percentage using the scoring engine
        pv = serializer.validated_data.get('progress_value', 0)
        progress_percentage = calculate_progress_percentage(goal, pv)

        checkin = serializer.save(user=user, progress_percentage=progress_percentage)

        # Audit trail — Task 22
        log_audit_trail(
            entity_type='checkin',
            entity_id=checkin.id,
            action='create',
            user=request.user,
            new_values={
                'goal_id': checkin.goal_id,
                'goal_title': goal.title,
                'cycle_id': checkin.cycle_id,
                'progress_value': checkin.progress_value,
                'progress_percentage': checkin.progress_percentage,
                'status': checkin.status,
            },
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
        )

        # Notify manager that a check-in is pending review
        if user.profile.manager:
            send_notification(
                user=user.profile.manager,
                title='Check-in Pending Review',
                message=f'{user.username} submitted a check-in for goal "{goal.title}"',
                notification_type='checkin_pending_review',
                checkin=checkin,
            )

        return Response(CheckInSerializer(checkin).data, status=status.HTTP_201_CREATED)

    # ------------------------------------------------------------------
    # Task 19: POST /api/checkins/{id}/submit/
    # ------------------------------------------------------------------

    @action(detail=True, methods=['post'])
    def submit(self, request, pk=None):
        """
        Submit a check-in with a progress value.

        This endpoint allows an employee to update the progress value on an
        existing check-in and formally submit it for manager review.

        Validates:
        - Check-in belongs to the requesting user
        - Check-in is in 'submitted' status (idempotent re-submit is rejected)
        - Progress value is valid for the goal's UoM type
        - Quarterly check-in period is active

        Requirements: 8.3, 8.4, 8.5, 8.6, 8.7, 8.8
        """
        from .validators import CheckInValidator

        checkin = self.get_object()
        user = request.user

        # Only the owner can submit
        if checkin.user != user and user.profile.role not in ['manager', 'admin']:
            raise PermissionDenied("You can only submit your own check-ins.")

        # Already submitted / approved / rejected
        if checkin.status != 'submitted':
            # Allow re-submission only if rejected
            if checkin.status == 'approved':
                return Response(
                    {'error': 'Approved check-ins cannot be re-submitted'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        progress_value = request.data.get('progress_value', checkin.progress_value)
        comments = request.data.get('comments', checkin.comments)

        # Validate quarterly period
        try:
            CheckInValidator.validate_checkin_period(checkin.cycle)
        except (ValidationError, DjangoValidationError) as e:
            msg = e.message if isinstance(e, DjangoValidationError) and hasattr(e, 'message') else str(e)
            from .utils import validate_checkin_period as util_validate_period
            _, next_date, _ = util_validate_period(checkin.cycle)
            return Response(
                {
                    'error': msg,
                    'next_checkin_date': str(next_date) if next_date else None,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Validate progress value against UoM constraints
        try:
            CheckInValidator.validate_progress_value(checkin.goal, progress_value)
        except (ValidationError, DjangoValidationError) as e:
            msg = e.message if isinstance(e, DjangoValidationError) and hasattr(e, 'message') else str(e)
            return Response({'error': msg}, status=status.HTTP_400_BAD_REQUEST)

        old_values = {
            'progress_value': checkin.progress_value,
            'progress_percentage': checkin.progress_percentage,
            'status': checkin.status,
            'comments': checkin.comments,
        }

        # Recalculate progress percentage
        checkin.progress_value = float(progress_value)
        checkin.progress_percentage = calculate_progress_percentage(checkin.goal, checkin.progress_value)
        checkin.comments = comments
        checkin.status = 'submitted'
        checkin.save()

        # Audit trail — Task 22
        log_audit_trail(
            entity_type='checkin',
            entity_id=checkin.id,
            action='submit',
            user=request.user,
            old_values=old_values,
            new_values={
                'progress_value': checkin.progress_value,
                'progress_percentage': checkin.progress_percentage,
                'status': checkin.status,
                'comments': checkin.comments,
            },
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
        )

        # Notify manager
        if user.profile.manager:
            send_notification(
                user=user.profile.manager,
                title='Check-in Pending Review',
                message=f'{user.username} submitted a check-in for goal "{checkin.goal.title}"',
                notification_type='checkin_pending_review',
                checkin=checkin,
            )

        return Response(CheckInSerializer(checkin).data)

    # ------------------------------------------------------------------
    # Task 21: GET /api/checkins/pending/
    # ------------------------------------------------------------------

    @action(detail=False, methods=['get'])
    def pending(self, request):
        """
        Return all pending (submitted) check-ins for manager review.

        Managers see submitted check-ins from their direct reports only.
        Admins see all submitted check-ins.

        Requirements: 14.1, 14.2
        """
        user = request.user

        if not hasattr(user, 'profile') or user.profile.role not in ['manager', 'admin']:
            raise PermissionDenied("Only managers and admins can view pending check-ins.")

        if user.profile.role == 'admin':
            pending_checkins = CheckIn.objects.filter(status='submitted')
        else:
            pending_checkins = CheckIn.objects.filter(
                status='submitted',
                user__profile__manager=user,
            )

        serializer = CheckInSerializer(pending_checkins, many=True)
        return Response(serializer.data)

    # ------------------------------------------------------------------
    # Task 21: POST /api/checkins/{id}/approve/
    # ------------------------------------------------------------------

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """
        Approve a submitted check-in.

        Records the approving manager's ID and the approval timestamp.
        Sends a notification to the employee.
        Logs the action to the audit trail.

        Requirements: 14.3, 14.4, 14.5, 14.6
        """
        checkin = self.get_object()
        user = request.user
        approval_comments = request.data.get('approval_comments', '')

        if not hasattr(user, 'profile') or user.profile.role not in ['manager', 'admin']:
            raise PermissionDenied("Only managers and admins can approve check-ins.")

        if checkin.status != 'submitted':
            return Response(
                {'error': 'Only submitted check-ins can be approved'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        checkin.status = 'approved'
        checkin.approved_by = user
        checkin.approved_at = timezone.now()
        checkin.save()

        # Audit trail — Task 22
        log_audit_trail(
            entity_type='checkin',
            entity_id=checkin.id,
            action='approve',
            user=request.user,
            old_values={'status': 'submitted'},
            new_values={
                'status': 'approved',
                'approved_by': user.username,
                'approved_by_id': user.id,
                'approved_at': str(checkin.approved_at),
                'approval_comments': approval_comments,
            },
            comments=approval_comments,
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
        )

        send_notification(
            user=checkin.user,
            title='Check-in Approved',
            message=f'Your check-in for goal "{checkin.goal.title}" has been approved'
                    + (f'. Comments: {approval_comments}' if approval_comments else ''),
            notification_type='checkin_approved',
            checkin=checkin,
        )

        return Response(CheckInSerializer(checkin).data)

    # ------------------------------------------------------------------
    # Task 21: POST /api/checkins/{id}/reject/
    # ------------------------------------------------------------------

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """
        Reject a submitted check-in with mandatory comments.

        Sends a notification to the employee.
        Logs the action to the audit trail.

        Requirements: 14.3, 14.4, 14.5, 14.7
        """
        checkin = self.get_object()
        user = request.user
        rejection_comments = request.data.get('rejection_comments', '')

        if not hasattr(user, 'profile') or user.profile.role not in ['manager', 'admin']:
            raise PermissionDenied("Only managers and admins can reject check-ins.")

        if checkin.status != 'submitted':
            return Response(
                {'error': 'Only submitted check-ins can be rejected'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not rejection_comments:
            return Response(
                {'error': 'Rejection comments are required'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        checkin.status = 'rejected'
        checkin.rejection_comments = rejection_comments
        checkin.save()

        # Audit trail — Task 22
        log_audit_trail(
            entity_type='checkin',
            entity_id=checkin.id,
            action='reject',
            user=request.user,
            old_values={'status': 'submitted'},
            new_values={
                'status': 'rejected',
                'rejection_comments': rejection_comments,
            },
            comments=rejection_comments,
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
        )

        send_notification(
            user=checkin.user,
            title='Check-in Rejected',
            message=f'Your check-in for goal "{checkin.goal.title}" has been rejected. Comments: {rejection_comments}',
            notification_type='checkin_rejected',
            checkin=checkin,
        )

        return Response(CheckInSerializer(checkin).data)


# ============================================================================
# Notification ViewSet
# ============================================================================

class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for Notification management (read-only)."""

    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticatedUser]

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user).order_by('-created_at')

    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        notif = self.get_object()
        notif.is_read = True
        notif.read_at = timezone.now()
        notif.save()
        return Response(self.get_serializer(notif).data)

    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        Notification.objects.filter(user=request.user, is_read=False).update(
            is_read=True, read_at=timezone.now()
        )
        return Response({'status': 'ok'})
