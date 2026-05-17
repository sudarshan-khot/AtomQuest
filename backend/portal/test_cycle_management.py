"""
Tests for Cycle Management (Task 17).

Tests for:
- Cycle creation with automatic check-in dates
- Cycle status transitions (Planning → Active → Closed)
- Cycle activation and closure
- Audit trail logging for cycle operations
- Admin-only access control
- Cycle-based constraints on goal and check-in operations
"""
from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import datetime, timedelta
from rest_framework.test import APITestCase, APIClient
from rest_framework import status

from .models import (
    UserProfile, Department, Cycle, Goal, CheckIn, AuditLog, ThrustArea, UoMType
)


class CycleManagementTestCase(APITestCase):
    """Test cases for cycle management endpoints."""
    
    def setUp(self):
        """Set up test data."""
        # Create admin user
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@test.com',
            password='testpass123'
        )
        self.admin_profile = UserProfile.objects.create(
            user=self.admin_user,
            role='admin'
        )
        
        # Create manager user
        self.manager_user = User.objects.create_user(
            username='manager',
            email='manager@test.com',
            password='testpass123'
        )
        self.manager_profile = UserProfile.objects.create(
            user=self.manager_user,
            role='manager'
        )
        
        # Create employee user
        self.employee_user = User.objects.create_user(
            username='employee',
            email='employee@test.com',
            password='testpass123'
        )
        self.employee_profile = UserProfile.objects.create(
            user=self.employee_user,
            role='employee',
            manager=self.manager_user
        )
        
        self.client = APIClient()
    
    # ========================================================================
    # Cycle Creation Tests
    # ========================================================================
    
    def test_admin_can_create_cycle(self):
        """Test that admin can create a new cycle."""
        self.client.force_authenticate(user=self.admin_user)
        
        cycle_data = {
            'name': 'FY2024 Q1',
            'description': 'First quarter of fiscal year 2024',
            'start_date': '2024-01-01',
            'end_date': '2024-03-31'
        }
        
        response = self.client.post('/api/cycles/', cycle_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'FY2024 Q1')
        self.assertEqual(response.data['status'], 'planning')
        
        # Verify cycle was created
        cycle = Cycle.objects.get(id=response.data['id'])
        self.assertEqual(cycle.name, 'FY2024 Q1')
        self.assertEqual(cycle.status, 'planning')
    
    def test_cycle_creation_sets_checkin_dates(self):
        """Test that cycle creation automatically sets check-in dates."""
        self.client.force_authenticate(user=self.admin_user)
        
        cycle_data = {
            'name': 'FY2024',
            'start_date': '2024-01-01',
            'end_date': '2024-12-31'
        }
        
        response = self.client.post('/api/cycles/', cycle_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify check-in dates are set
        cycle = Cycle.objects.get(id=response.data['id'])
        self.assertIsNotNone(cycle.checkin_date_q1)
        self.assertIsNotNone(cycle.checkin_date_q2)
        self.assertIsNotNone(cycle.checkin_date_q3)
        self.assertIsNotNone(cycle.checkin_date_q4)
        
        # Verify dates are in correct months
        self.assertEqual(cycle.checkin_date_q1.month, 7)  # July
        self.assertEqual(cycle.checkin_date_q2.month, 10)  # October
        self.assertEqual(cycle.checkin_date_q3.month, 1)  # January
        self.assertEqual(cycle.checkin_date_q4.month, 4)  # April
    
    def test_cycle_creation_logs_audit_trail(self):
        """Test that cycle creation is logged in audit trail."""
        self.client.force_authenticate(user=self.admin_user)
        
        cycle_data = {
            'name': 'FY2024 Q1',
            'start_date': '2024-01-01',
            'end_date': '2024-03-31'
        }
        
        response = self.client.post('/api/cycles/', cycle_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify audit log entry
        audit_logs = AuditLog.objects.filter(
            entity_type='cycle',
            entity_id=response.data['id'],
            action='create'
        )
        
        self.assertEqual(audit_logs.count(), 1)
        audit_log = audit_logs.first()
        self.assertEqual(audit_log.user, self.admin_user)
        self.assertIn('name', audit_log.new_values)
        self.assertEqual(audit_log.new_values['name'], 'FY2024 Q1')
    
    def test_non_admin_cannot_create_cycle(self):
        """Test that non-admin users cannot create cycles."""
        self.client.force_authenticate(user=self.employee_user)
        
        cycle_data = {
            'name': 'FY2024 Q1',
            'start_date': '2024-01-01',
            'end_date': '2024-03-31'
        }
        
        response = self.client.post('/api/cycles/', cycle_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_manager_cannot_create_cycle(self):
        """Test that managers cannot create cycles."""
        self.client.force_authenticate(user=self.manager_user)
        
        cycle_data = {
            'name': 'FY2024 Q1',
            'start_date': '2024-01-01',
            'end_date': '2024-03-31'
        }
        
        response = self.client.post('/api/cycles/', cycle_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    # ========================================================================
    # Cycle Activation Tests
    # ========================================================================
    
    def test_admin_can_activate_cycle(self):
        """Test that admin can activate a cycle."""
        # Create a cycle in planning status
        cycle = Cycle.objects.create(
            name='FY2024 Q1',
            start_date='2024-01-01',
            end_date='2024-03-31',
            status='planning'
        )
        
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.post(f'/api/cycles/{cycle.id}/activate/', format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'active')
        
        # Verify cycle status was updated
        cycle.refresh_from_db()
        self.assertEqual(cycle.status, 'active')
    
    def test_cycle_activation_logs_audit_trail(self):
        """Test that cycle activation is logged in audit trail."""
        cycle = Cycle.objects.create(
            name='FY2024 Q1',
            start_date='2024-01-01',
            end_date='2024-03-31',
            status='planning'
        )
        
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.post(f'/api/cycles/{cycle.id}/activate/', format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify audit log entry
        audit_logs = AuditLog.objects.filter(
            entity_type='cycle',
            entity_id=cycle.id,
            action='update'
        )
        
        self.assertEqual(audit_logs.count(), 1)
        audit_log = audit_logs.first()
        self.assertEqual(audit_log.old_values['status'], 'planning')
        self.assertEqual(audit_log.new_values['status'], 'active')
    
    def test_cannot_activate_non_planning_cycle(self):
        """Test that only planning cycles can be activated."""
        cycle = Cycle.objects.create(
            name='FY2024 Q1',
            start_date='2024-01-01',
            end_date='2024-03-31',
            status='active'
        )
        
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.post(f'/api/cycles/{cycle.id}/activate/', format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
    
    def test_non_admin_cannot_activate_cycle(self):
        """Test that non-admin users cannot activate cycles."""
        cycle = Cycle.objects.create(
            name='FY2024 Q1',
            start_date='2024-01-01',
            end_date='2024-03-31',
            status='planning'
        )
        
        self.client.force_authenticate(user=self.employee_user)
        response = self.client.post(f'/api/cycles/{cycle.id}/activate/', format='json')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    # ========================================================================
    # Cycle Closure Tests
    # ========================================================================
    
    def test_admin_can_close_cycle(self):
        """Test that admin can close an active cycle."""
        cycle = Cycle.objects.create(
            name='FY2024 Q1',
            start_date='2024-01-01',
            end_date='2024-03-31',
            status='active'
        )
        
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.post(f'/api/cycles/{cycle.id}/close/', format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'closed')
        
        # Verify cycle status was updated
        cycle.refresh_from_db()
        self.assertEqual(cycle.status, 'closed')
    
    def test_cycle_closure_logs_audit_trail(self):
        """Test that cycle closure is logged in audit trail."""
        cycle = Cycle.objects.create(
            name='FY2024 Q1',
            start_date='2024-01-01',
            end_date='2024-03-31',
            status='active'
        )
        
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.post(f'/api/cycles/{cycle.id}/close/', format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify audit log entry
        audit_logs = AuditLog.objects.filter(
            entity_type='cycle',
            entity_id=cycle.id,
            action='update'
        )
        
        self.assertEqual(audit_logs.count(), 1)
        audit_log = audit_logs.first()
        self.assertEqual(audit_log.old_values['status'], 'active')
        self.assertEqual(audit_log.new_values['status'], 'closed')
    
    def test_cannot_close_non_active_cycle(self):
        """Test that only active cycles can be closed."""
        cycle = Cycle.objects.create(
            name='FY2024 Q1',
            start_date='2024-01-01',
            end_date='2024-03-31',
            status='planning'
        )
        
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.post(f'/api/cycles/{cycle.id}/close/', format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
    
    def test_non_admin_cannot_close_cycle(self):
        """Test that non-admin users cannot close cycles."""
        cycle = Cycle.objects.create(
            name='FY2024 Q1',
            start_date='2024-01-01',
            end_date='2024-03-31',
            status='active'
        )
        
        self.client.force_authenticate(user=self.employee_user)
        response = self.client.post(f'/api/cycles/{cycle.id}/close/', format='json')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    # ========================================================================
    # Cycle Status Transition Tests
    # ========================================================================
    
    def test_cycle_status_transitions_follow_state_machine(self):
        """Test that cycle status transitions follow valid state machine."""
        cycle = Cycle.objects.create(
            name='FY2024 Q1',
            start_date='2024-01-01',
            end_date='2024-03-31',
            status='planning'
        )
        
        self.client.force_authenticate(user=self.admin_user)
        
        # Planning → Active
        response = self.client.post(f'/api/cycles/{cycle.id}/activate/', format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'active')
        
        # Active → Closed
        response = self.client.post(f'/api/cycles/{cycle.id}/close/', format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'closed')
        
        # Closed → Active (should fail)
        response = self.client.post(f'/api/cycles/{cycle.id}/activate/', format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    # ========================================================================
    # Cycle Listing Tests
    # ========================================================================
    
    def test_admin_can_list_cycles(self):
        """Test that admin can list all cycles."""
        # Create multiple cycles
        Cycle.objects.create(
            name='FY2024 Q1',
            start_date='2024-01-01',
            end_date='2024-03-31',
            status='planning'
        )
        Cycle.objects.create(
            name='FY2024 Q2',
            start_date='2024-04-01',
            end_date='2024-06-30',
            status='active'
        )
        
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get('/api/cycles/', format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
    
    def test_non_admin_cannot_list_cycles(self):
        """Test that non-admin users cannot list cycles."""
        self.client.force_authenticate(user=self.employee_user)
        response = self.client.get('/api/cycles/', format='json')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    # ========================================================================
    # Cycle-Based Constraints Tests
    # ========================================================================
    
    def test_goal_creation_prevented_in_planning_cycle(self):
        """Test that goals cannot be created in planning cycles."""
        # Create a planning cycle
        cycle = Cycle.objects.create(
            name='FY2024 Q1',
            start_date='2024-01-01',
            end_date='2024-03-31',
            status='planning'
        )
        
        # Create thrust area and UoM type
        thrust_area = ThrustArea.objects.create(name='Revenue Growth')
        uom_type = UoMType.objects.create(name='numeric')
        
        self.client.force_authenticate(user=self.employee_user)
        
        goal_data = {
            'title': 'Increase Revenue',
            'description': 'Increase revenue by 20%',
            'cycle': cycle.id,
            'thrust_area': thrust_area.id,
            'uom_type': uom_type.id,
            'target_value': 100000,
            'weightage': 50
        }
        
        response = self.client.post('/api/goals/', goal_data, format='json')
        
        # Should fail because cycle is in planning status
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
    
    def test_goal_creation_allowed_in_active_cycle(self):
        """Test that goals can be created in active cycles."""
        # Create an active cycle
        cycle = Cycle.objects.create(
            name='FY2024 Q1',
            start_date='2024-01-01',
            end_date='2024-03-31',
            status='active'
        )
        
        # Create thrust area and UoM type
        thrust_area = ThrustArea.objects.create(name='Revenue Growth')
        uom_type = UoMType.objects.create(name='numeric')
        
        self.client.force_authenticate(user=self.employee_user)
        
        goal_data = {
            'title': 'Increase Revenue',
            'description': 'Increase revenue by 20%',
            'cycle': cycle.id,
            'thrust_area': thrust_area.id,
            'uom_type': uom_type.id,
            'target_value': 100000,
            'weightage': 100
        }
        
        response = self.client.post('/api/goals/', goal_data, format='json')
        
        # Should succeed because cycle is active
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
    
    def test_goal_creation_prevented_in_closed_cycle(self):
        """Test that goals cannot be created in closed cycles."""
        # Create a closed cycle
        cycle = Cycle.objects.create(
            name='FY2024 Q1',
            start_date='2024-01-01',
            end_date='2024-03-31',
            status='closed'
        )
        
        # Create thrust area and UoM type
        thrust_area = ThrustArea.objects.create(name='Revenue Growth')
        uom_type = UoMType.objects.create(name='numeric')
        
        self.client.force_authenticate(user=self.employee_user)
        
        goal_data = {
            'title': 'Increase Revenue',
            'description': 'Increase revenue by 20%',
            'cycle': cycle.id,
            'thrust_area': thrust_area.id,
            'uom_type': uom_type.id,
            'target_value': 100000,
            'weightage': 100
        }
        
        response = self.client.post('/api/goals/', goal_data, format='json')
        
        # Should fail because cycle is closed
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)


class CycleAuditTrailTestCase(APITestCase):
    """Test cases for cycle audit trail logging."""
    
    def setUp(self):
        """Set up test data."""
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@test.com',
            password='testpass123'
        )
        self.admin_profile = UserProfile.objects.create(
            user=self.admin_user,
            role='admin'
        )
        
        self.client = APIClient()
    
    def test_audit_trail_captures_ip_address(self):
        """Test that audit trail captures IP address."""
        self.client.force_authenticate(user=self.admin_user)
        
        cycle_data = {
            'name': 'FY2024 Q1',
            'start_date': '2024-01-01',
            'end_date': '2024-03-31'
        }
        
        response = self.client.post('/api/cycles/', cycle_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify audit log has IP address
        audit_log = AuditLog.objects.filter(
            entity_type='cycle',
            entity_id=response.data['id']
        ).first()
        
        self.assertIsNotNone(audit_log.ip_address)
    
    def test_audit_trail_captures_user_agent(self):
        """Test that audit trail captures user agent."""
        self.client.force_authenticate(user=self.admin_user)
        
        cycle_data = {
            'name': 'FY2024 Q1',
            'start_date': '2024-01-01',
            'end_date': '2024-03-31'
        }
        
        response = self.client.post('/api/cycles/', cycle_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify audit log has user agent
        audit_log = AuditLog.objects.filter(
            entity_type='cycle',
            entity_id=response.data['id']
        ).first()
        
        # User agent might be empty in test, but field should exist
        self.assertIsNotNone(audit_log.user_agent)
    
    def test_audit_trail_records_all_cycle_operations(self):
        """Test that audit trail records all cycle operations."""
        cycle = Cycle.objects.create(
            name='FY2024 Q1',
            start_date='2024-01-01',
            end_date='2024-03-31',
            status='planning'
        )
        
        self.client.force_authenticate(user=self.admin_user)
        
        # Activate cycle
        self.client.post(f'/api/cycles/{cycle.id}/activate/', format='json')
        
        # Close cycle
        self.client.post(f'/api/cycles/{cycle.id}/close/', format='json')
        
        # Verify audit logs
        audit_logs = AuditLog.objects.filter(
            entity_type='cycle',
            entity_id=cycle.id
        ).order_by('created_at')
        
        self.assertEqual(audit_logs.count(), 2)
        self.assertEqual(audit_logs[0].action, 'update')
        self.assertEqual(audit_logs[0].old_values['status'], 'planning')
        self.assertEqual(audit_logs[0].new_values['status'], 'active')
        
        self.assertEqual(audit_logs[1].action, 'update')
        self.assertEqual(audit_logs[1].old_values['status'], 'active')
        self.assertEqual(audit_logs[1].new_values['status'], 'closed')
