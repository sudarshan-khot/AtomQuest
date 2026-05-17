"""
Management command to seed initial data for development.
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from portal.models import Goal, Milestone, Habit, Progress


class Command(BaseCommand):
    help = 'Seed initial data for development'

    def handle(self, *args, **options):
        # Create test user
        user, created = User.objects.get_or_create(
            username='testuser',
            defaults={
                'email': 'test@example.com',
                'first_name': 'Test',
                'last_name': 'User',
            }
        )
        if created:
            user.set_password('testpass123')
            user.save()
            self.stdout.write(self.style.SUCCESS('Created test user'))
        else:
            self.stdout.write(self.style.WARNING('Test user already exists'))

        # Create sample goals
        goal1, created = Goal.objects.get_or_create(
            user=user,
            title='Learn Django',
            defaults={
                'description': 'Master Django framework and build production-ready applications',
                'status': 'active',
                'priority': 'high',
                'target_value': 100,
                'current_value': 30,
                'unit': 'hours',
                'target_date': timezone.now() + timedelta(days=90),
                'category': 'Learning',
                'tags': 'programming,python,web-development',
            }
        )
        if created:
            goal1.calculate_progress()
            goal1.save()
            self.stdout.write(self.style.SUCCESS('Created goal: Learn Django'))

        goal2, created = Goal.objects.get_or_create(
            user=user,
            title='Fitness Goal',
            defaults={
                'description': 'Run 5km without stopping',
                'status': 'active',
                'priority': 'medium',
                'target_value': 5,
                'current_value': 2.5,
                'unit': 'km',
                'target_date': timezone.now() + timedelta(days=60),
                'category': 'Health',
                'tags': 'fitness,running,health',
            }
        )
        if created:
            goal2.calculate_progress()
            goal2.save()
            self.stdout.write(self.style.SUCCESS('Created goal: Fitness Goal'))

        # Create milestones for goal1
        milestone1, created = Milestone.objects.get_or_create(
            goal=goal1,
            title='Complete Django Basics',
            defaults={
                'description': 'Learn Django models, views, and templates',
                'status': 'in_progress',
                'target_value': 25,
                'current_value': 20,
                'target_date': timezone.now() + timedelta(days=30),
                'order': 1,
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS('Created milestone: Complete Django Basics'))

        milestone2, created = Milestone.objects.get_or_create(
            goal=goal1,
            title='Build REST API',
            defaults={
                'description': 'Create a complete REST API with Django REST Framework',
                'status': 'pending',
                'target_value': 40,
                'current_value': 0,
                'target_date': timezone.now() + timedelta(days=60),
                'order': 2,
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS('Created milestone: Build REST API'))

        # Create progress entries
        progress1, created = Progress.objects.get_or_create(
            goal=goal1,
            recorded_at=timezone.now() - timedelta(days=5),
            defaults={
                'value': 10,
                'note': 'Completed Django installation and setup',
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS('Created progress entry'))

        # Create habits
        habit1, created = Habit.objects.get_or_create(
            user=user,
            title='Morning Exercise',
            defaults={
                'description': 'Do 30 minutes of exercise every morning',
                'frequency': 'daily',
                'status': 'active',
                'streak_count': 5,
                'longest_streak': 10,
                'completion_count': 25,
                'goal': goal2,
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS('Created habit: Morning Exercise'))

        habit2, created = Habit.objects.get_or_create(
            user=user,
            title='Read Documentation',
            defaults={
                'description': 'Read Django documentation for 1 hour',
                'frequency': 'daily',
                'status': 'active',
                'streak_count': 3,
                'longest_streak': 7,
                'completion_count': 15,
                'goal': goal1,
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS('Created habit: Read Documentation'))

        self.stdout.write(self.style.SUCCESS('Successfully seeded initial data'))
