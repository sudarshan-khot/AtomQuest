"""
Celery app for atomquest project.
"""

import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'atomquest.settings')

try:
    from celery import Celery
    
    app = Celery('atomquest')
    
    # Load configuration from Django settings, all configuration keys should have a `CELERY_` prefix.
    app.config_from_object('django.conf:settings', namespace='CELERY')
    
    # Auto-discover tasks from all registered Django app configs.
    app.autodiscover_tasks()
    
    
    @app.task(bind=True)
    def debug_task(self):
        print(f'Request: {self.request!r}')
except ImportError:
    # Celery not installed, create a dummy app for testing
    class DummyApp:
        def autodiscover_tasks(self):
            pass
    
    app = DummyApp()
