from django.db import models
from django.conf import settings
from django.utils import timezone



class ReadingSchedule(models.Model):
    DAY_CHOICES = [
        (0, 'Monday'), (1, 'Tuesday'), (2, 'Wednesday'),
        (3, 'Thursday'), (4, 'Friday'), (5, 'Saturday'), (6, 'Sunday'),
    ]
    SESSION_CHOICES = [
        ('Career', 'Career-Specific Reading'),
        ('Self-Dev', 'Self-Development Reading'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='schedules')
    day_of_week = models.IntegerField(choices=DAY_CHOICES)
    session_type = models.CharField(max_length=20, choices=SESSION_CHOICES)
    start_time = models.TimeField()
    end_time = models.TimeField()

    class Meta:
        ordering = ['day_of_week', 'start_time']

    def __str__(self):
        return f"{self.user.username} - {self.get_day_of_week_display()} - {self.session_type}"


class Book(models.Model):
    STATUS_CHOICES = [
        ('Reading', 'Currently Reading'),
        ('Completed', 'Completed'),
        ('ToRead', 'To Read'),
    ]
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='books')
    title = models.CharField(max_length=255)
    author = models.CharField(max_length=255)
    category = models.CharField(max_length=20, choices=ReadingSchedule.SESSION_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ToRead')
    current_page = models.IntegerField(default=0)
    total_pages = models.IntegerField(default=0)
    cover_image = models.URLField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.title} by {self.author}"


class ReadingSession(models.Model):
    SESSION_CHOICES = [
        ('Career', 'Career-Specific Reading'),
        ('Self-Dev', 'Self-Development Reading'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sessions')
    schedule = models.ForeignKey(ReadingSchedule, on_delete=models.SET_NULL, null=True, blank=True)
    session_type = models.CharField(max_length=20, choices=SESSION_CHOICES)
    started_at = models.DateTimeField(default=timezone.now)
    ended_at = models.DateTimeField(null=True, blank=True)
    book = models.ForeignKey(Book, on_delete=models.SET_NULL, null=True, blank=True, related_name='sessions')
    start_page = models.IntegerField(null=True, blank=True)
    end_page = models.IntegerField(null=True, blank=True)
    notes = models.TextField(blank=True, default='')

    class Meta:
        ordering = ['-started_at']

    def __str__(self):
        return f"{self.user.username} - {self.session_type} - {self.started_at.date()}"

    @property
    def duration_minutes(self):
        if self.ended_at:
            delta = self.ended_at - self.started_at
            return round(delta.total_seconds() / 60, 1)
        return None

    @property
    def is_active(self):
        return self.ended_at is None
