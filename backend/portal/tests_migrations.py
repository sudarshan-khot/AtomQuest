"""
Tests for database migrations and reference data seeding.
"""
from django.test import TestCase
from django.core.management import call_command
from portal.models import ThrustArea, UoMType, Department


class MigrationTests(TestCase):
    """Test database migrations and reference data seeding."""
    
    def test_uom_types_seeded(self):
        """Test that UoM types are properly seeded."""
        # Call the seed command
        call_command('seed_reference_data')
        
        # Verify all UoM types exist
        expected_uom_types = ['numeric', 'percentage', 'timeline', 'zero_based']
        for uom_name in expected_uom_types:
            uom = UoMType.objects.get(name=uom_name)
            self.assertIsNotNone(uom)
            self.assertTrue(uom.is_active)
            self.assertIn(uom_name, uom.description.lower())
    
    def test_thrust_areas_seeded(self):
        """Test that thrust areas are properly seeded."""
        # Call the seed command
        call_command('seed_reference_data')
        
        # Verify all thrust areas exist
        expected_areas = [
            'Revenue Growth',
            'Customer Satisfaction',
            'Operational Excellence',
            'Innovation',
            'Team Development',
            'Cost Optimization',
            'Market Expansion',
            'Quality Improvement',
        ]
        for area_name in expected_areas:
            area = ThrustArea.objects.get(name=area_name)
            self.assertIsNotNone(area)
            self.assertTrue(area.is_active)
            self.assertGreater(len(area.description), 0)
    
    def test_departments_seeded(self):
        """Test that departments are properly seeded."""
        # Call the seed command
        call_command('seed_reference_data')
        
        # Verify all departments exist
        expected_departments = [
            'Sales',
            'Marketing',
            'Engineering',
            'Operations',
            'Human Resources',
            'Finance',
            'Customer Success',
        ]
        for dept_name in expected_departments:
            dept = Department.objects.get(name=dept_name)
            self.assertIsNotNone(dept)
            self.assertTrue(dept.is_active)
            self.assertGreater(len(dept.description), 0)
    
    def test_seed_command_idempotent(self):
        """Test that seed command is idempotent (can be run multiple times)."""
        # Call the seed command twice
        call_command('seed_reference_data')
        initial_uom_count = UoMType.objects.count()
        initial_area_count = ThrustArea.objects.count()
        initial_dept_count = Department.objects.count()
        
        call_command('seed_reference_data')
        
        # Verify counts haven't changed
        self.assertEqual(UoMType.objects.count(), initial_uom_count)
        self.assertEqual(ThrustArea.objects.count(), initial_area_count)
        self.assertEqual(Department.objects.count(), initial_dept_count)
    
    def test_uom_type_choices(self):
        """Test that UoM type choices match the model definition."""
        call_command('seed_reference_data')
        
        # Get all UoM types
        uom_types = UoMType.objects.all()
        
        # Verify they match the choices
        expected_choices = ['numeric', 'percentage', 'timeline', 'zero_based']
        actual_names = [uom.name for uom in uom_types]
        
        for choice in expected_choices:
            self.assertIn(choice, actual_names)
    
    def test_reference_data_descriptions(self):
        """Test that reference data has meaningful descriptions."""
        call_command('seed_reference_data')
        
        # Check UoM types have descriptions
        for uom in UoMType.objects.all():
            self.assertGreater(len(uom.description), 0)
        
        # Check thrust areas have descriptions
        for area in ThrustArea.objects.all():
            self.assertGreater(len(area.description), 0)
        
        # Check departments have descriptions
        for dept in Department.objects.all():
            self.assertGreater(len(dept.description), 0)
    
    def test_reference_data_active_status(self):
        """Test that all seeded reference data is active by default."""
        call_command('seed_reference_data')
        
        # Check all UoM types are active
        for uom in UoMType.objects.all():
            self.assertTrue(uom.is_active)
        
        # Check all thrust areas are active
        for area in ThrustArea.objects.all():
            self.assertTrue(area.is_active)
        
        # Check all departments are active
        for dept in Department.objects.all():
            self.assertTrue(dept.is_active)
