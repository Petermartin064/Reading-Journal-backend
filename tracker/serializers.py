from rest_framework import serializers
from .models import ReadingSchedule, ReadingSession, Book


class ReadingScheduleSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReadingSchedule
        fields = ['id', 'day_of_week', 'session_type', 'start_time', 'end_time']
        read_only_fields = ['id']

    def validate(self, attrs):
        start = attrs.get('start_time')
        end = attrs.get('end_time')
        if start and end and start >= end:
            raise serializers.ValidationError("start_time must be before end_time.")
        return attrs

class BookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = ['id', 'title', 'author', 'category', 'status', 'current_page', 'total_pages', 'cover_image', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class ReadingSessionSerializer(serializers.ModelSerializer):
    duration_minutes = serializers.ReadOnlyField()
    is_active = serializers.ReadOnlyField()
    book_title = serializers.CharField(source='book.title', read_only=True)
    book_author = serializers.CharField(source='book.author', read_only=True)

    class Meta:
        model = ReadingSession
        fields = [
            'id', 'session_type', 'schedule', 'book', 'book_title', 'book_author', 
            'started_at', 'ended_at', 'duration_minutes', 'is_active', 
            'start_page', 'end_page', 'is_paused', 'last_paused_at', 'total_paused_seconds', 
            'last_heartbeat_at', 'notes'
        ]
        read_only_fields = ['started_at', 'ended_at', 'duration_minutes', 'is_active']
