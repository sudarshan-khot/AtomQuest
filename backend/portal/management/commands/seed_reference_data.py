"""
Management command to seed reference data for AtomQuest.
"""
from django.core.management.base import BaseCommand
from datetime import date
from portal.models import ThrustArea, UoMType, Department, Cycle


class Command(BaseCommand):
    help = 'Seed reference data for AtomQuest'

    def handle(self, *args, **options):
        self.stdout.write('Seeding reference data...')

        self._seed_uom_types()
        self._seed_thrust_areas()
        self._seed_departments()
        self._seed_cycles()

        self.stdout.write(self.style.SUCCESS('Reference data seeding completed!'))

    # ── UoM Types ────────────────────────────────────────────────────────────

    def _seed_uom_types(self):
        uom_types = [
            ('numeric',    'Numeric values — progress = (current / target) × 100, capped at 100%'),
            ('percentage', 'Percentage values — direct mapping 0–100%'),
            ('timeline',   'Timeline-based — progress = (today − start) / (end − start) × 100'),
            ('zero_based', 'Zero-based — 0% if zero, 100% if any non-zero value'),
        ]
        for name, desc in uom_types:
            _, created = UoMType.objects.get_or_create(name=name, defaults={'description': desc})
            label = 'Created' if created else 'Exists '
            self.stdout.write(f'  UoM  [{label}] {name}')

    # ── Thrust Areas ─────────────────────────────────────────────────────────

    def _seed_thrust_areas(self):
        areas = [
            ('Revenue Growth',        'Goals related to increasing revenue and sales'),
            ('Customer Satisfaction', 'Goals related to improving customer experience'),
            ('Operational Excellence','Goals related to improving operations and efficiency'),
            ('Innovation',            'Goals related to new products and services'),
            ('Team Development',      'Goals related to employee growth and development'),
            ('Cost Optimization',     'Goals related to reducing costs and improving margins'),
            ('Market Expansion',      'Goals related to entering new markets'),
            ('Quality Improvement',   'Goals related to improving product/service quality'),
        ]
        for name, desc in areas:
            _, created = ThrustArea.objects.get_or_create(name=name, defaults={'description': desc})
            label = 'Created' if created else 'Exists '
            self.stdout.write(f'  Area [{label}] {name}')

    # ── Departments ───────────────────────────────────────────────────────────

    def _seed_departments(self):
        depts = [
            ('Sales',            'Sales and business development'),
            ('Marketing',        'Marketing and brand management'),
            ('Engineering',      'Product engineering and development'),
            ('Operations',       'Operations and process management'),
            ('Human Resources',  'Human resources and talent management'),
            ('Finance',          'Finance and accounting'),
            ('Customer Success', 'Customer support and success'),
        ]
        for name, desc in depts:
            _, created = Department.objects.get_or_create(name=name, defaults={'description': desc})
            label = 'Created' if created else 'Exists '
            self.stdout.write(f'  Dept [{label}] {name}')

    # ── Cycles ────────────────────────────────────────────────────────────────
    #
    # Per the AtomQuest problem statement the performance cycle runs April–March
    # (Indian financial year).  Quarterly check-in windows are:
    #   Q1 — July 15      (Apr–Jun review)
    #   Q2 — October 15   (Jul–Sep review)
    #   Q3 — January 15   (Oct–Dec review)
    #   Q4 — April 15     (Jan–Mar review, final)
    #
    # We seed:
    #   FY2024-25  — closed  (Apr 2024 – Mar 2025)
    #   FY2025-26  — active  (Apr 2025 – Mar 2026)  ← employees use this one
    #   FY2026-27  — planning (Apr 2026 – Mar 2027)

    def _seed_cycles(self):
        cycles = [
            {
                'name':        'FY2024-25',
                'description': 'Financial Year April 2024 – March 2025',
                'status':      'closed',
                'start_date':  date(2024, 4, 1),
                'end_date':    date(2025, 3, 31),
                'q1': date(2024, 7, 15),
                'q2': date(2024, 10, 15),
                'q3': date(2025, 1, 15),
                'q4': date(2025, 4, 15),
            },
            {
                'name':        'FY2025-26',
                'description': 'Financial Year April 2025 – March 2026 (current)',
                'status':      'active',
                'start_date':  date(2025, 4, 1),
                'end_date':    date(2026, 3, 31),
                'q1': date(2025, 7, 15),
                'q2': date(2025, 10, 15),
                'q3': date(2026, 1, 15),
                'q4': date(2026, 4, 15),
            },
            {
                'name':        'FY2026-27',
                'description': 'Financial Year April 2026 – March 2027 (planning)',
                'status':      'planning',
                'start_date':  date(2026, 4, 1),
                'end_date':    date(2027, 3, 31),
                'q1': date(2026, 7, 15),
                'q2': date(2026, 10, 15),
                'q3': date(2027, 1, 15),
                'q4': date(2027, 4, 15),
            },
        ]

        for c in cycles:
            cycle, created = Cycle.objects.get_or_create(
                name=c['name'],
                defaults={
                    'description':      c['description'],
                    'status':           c['status'],
                    'start_date':       c['start_date'],
                    'end_date':         c['end_date'],
                    'checkin_date_q1':  c['q1'],
                    'checkin_date_q2':  c['q2'],
                    'checkin_date_q3':  c['q3'],
                    'checkin_date_q4':  c['q4'],
                }
            )
            if not created:
                # Keep status and dates in sync on re-runs
                cycle.status          = c['status']
                cycle.checkin_date_q1 = c['q1']
                cycle.checkin_date_q2 = c['q2']
                cycle.checkin_date_q3 = c['q3']
                cycle.checkin_date_q4 = c['q4']
                cycle.save()

            label = 'Created' if created else 'Updated'
            self.stdout.write(
                f'  Cycle [{label}] {cycle.name} — {cycle.status}'
                f'  (Q1:{c["q1"]}  Q2:{c["q2"]}  Q3:{c["q3"]}  Q4:{c["q4"]})'
            )

