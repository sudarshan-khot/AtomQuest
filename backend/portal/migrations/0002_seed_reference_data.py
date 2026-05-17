# Generated migration to seed reference data for ThrustArea and UoMType

from django.db import migrations


def seed_reference_data(apps, schema_editor):
    """Seed default reference data for ThrustArea and UoMType."""
    ThrustArea = apps.get_model('portal', 'ThrustArea')
    UoMType = apps.get_model('portal', 'UoMType')
    
    # Seed UoM Types
    uom_types = [
        {
            'name': 'numeric',
            'description': 'Numeric values (e.g., revenue, units sold)'
        },
        {
            'name': 'percentage',
            'description': 'Percentage values (0-100%)'
        },
        {
            'name': 'timeline',
            'description': 'Timeline-based progress (start to end date)'
        },
        {
            'name': 'zero_based',
            'description': 'Zero-based (0% if zero, 100% if non-zero)'
        },
    ]
    
    for uom_data in uom_types:
        UoMType.objects.get_or_create(
            name=uom_data['name'],
            defaults={'description': uom_data['description']}
        )
    
    # Seed Thrust Areas
    thrust_areas = [
        {
            'name': 'Revenue Growth',
            'description': 'Goals related to increasing revenue and sales'
        },
        {
            'name': 'Customer Satisfaction',
            'description': 'Goals related to improving customer experience'
        },
        {
            'name': 'Operational Excellence',
            'description': 'Goals related to improving operations and efficiency'
        },
        {
            'name': 'Innovation',
            'description': 'Goals related to new products and services'
        },
        {
            'name': 'Team Development',
            'description': 'Goals related to employee growth and development'
        },
        {
            'name': 'Cost Optimization',
            'description': 'Goals related to reducing costs and improving margins'
        },
        {
            'name': 'Market Expansion',
            'description': 'Goals related to entering new markets'
        },
        {
            'name': 'Quality Improvement',
            'description': 'Goals related to improving product/service quality'
        },
    ]
    
    for area_data in thrust_areas:
        ThrustArea.objects.get_or_create(
            name=area_data['name'],
            defaults={'description': area_data['description']}
        )


def reverse_seed_reference_data(apps, schema_editor):
    """Reverse the seeding of reference data."""
    ThrustArea = apps.get_model('portal', 'ThrustArea')
    UoMType = apps.get_model('portal', 'UoMType')
    
    # Delete seeded UoM Types
    UoMType.objects.filter(name__in=['numeric', 'percentage', 'timeline', 'zero_based']).delete()
    
    # Delete seeded Thrust Areas
    ThrustArea.objects.filter(name__in=[
        'Revenue Growth',
        'Customer Satisfaction',
        'Operational Excellence',
        'Innovation',
        'Team Development',
        'Cost Optimization',
        'Market Expansion',
        'Quality Improvement',
    ]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('portal', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(seed_reference_data, reverse_seed_reference_data),
    ]
