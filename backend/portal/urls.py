"""
URL configuration for AtomQuest Goal Setting & Tracking Portal.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ThrustAreaViewSet, UoMTypeViewSet, DepartmentViewSet,
    UserProfileViewSet, UserManagementViewSet,
    CycleViewSet, GoalViewSet, CheckInViewSet, NotificationViewSet
)

router = DefaultRouter()

# Reference data
router.register(r'thrust-areas', ThrustAreaViewSet, basename='thrust-area')
router.register(r'uom-types', UoMTypeViewSet, basename='uom-type')
router.register(r'departments', DepartmentViewSet, basename='department')

# User management
router.register(r'users', UserProfileViewSet, basename='user-profile')
router.register(r'user-management', UserManagementViewSet, basename='user-management')

# Cycle management
router.register(r'cycles', CycleViewSet, basename='cycle')

# Goal management
router.register(r'goals', GoalViewSet, basename='goal')

# Check-in management
router.register(r'checkins', CheckInViewSet, basename='checkin')

# Notifications
router.register(r'notifications', NotificationViewSet, basename='notification')

urlpatterns = [
    path('', include(router.urls)),
]
