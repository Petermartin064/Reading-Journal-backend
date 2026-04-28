from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from datetime import time
from .models import ReadingSchedule

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def seed_default_schedule(sender, instance, created, **kwargs):
    if created:
        schedules = []
        
        # Weekdays (Monday=0 to Friday=4)
        for day in range(5):
            schedules.append(ReadingSchedule(
                user=instance, day_of_week=day, session_type='Career',
                start_time=time(5, 0), end_time=time(7, 30)
            ))
            schedules.append(ReadingSchedule(
                user=instance, day_of_week=day, session_type='Self-Dev',
                start_time=time(20, 0), end_time=time(21, 30)
            ))
            
        # Saturday (5)
        schedules.append(ReadingSchedule(
            user=instance, day_of_week=5, session_type='Career',
            start_time=time(6, 0), end_time=time(10, 0)
        ))
        schedules.append(ReadingSchedule(
            user=instance, day_of_week=5, session_type='Self-Dev',
            start_time=time(14, 0), end_time=time(18, 0)
        ))
        
        # Sunday (6)
        schedules.append(ReadingSchedule(
            user=instance, day_of_week=6, session_type='Career',
            start_time=time(6, 0), end_time=time(10, 0)
        ))
        schedules.append(ReadingSchedule(
            user=instance, day_of_week=6, session_type='Self-Dev',
            start_time=time(14, 0), end_time=time(17, 30)
        ))
        
        ReadingSchedule.objects.bulk_create(schedules)
