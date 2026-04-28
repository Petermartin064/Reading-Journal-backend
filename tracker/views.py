from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.utils import timezone
from datetime import timedelta
from .models import ReadingSchedule, ReadingSession, Book
from .serializers import ReadingScheduleSerializer, ReadingSessionSerializer, BookSerializer
from rest_framework import viewsets


class TodayScheduleView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        today_day_of_week = timezone.now().weekday()
        schedules = ReadingSchedule.objects.filter(
            user=request.user,
            day_of_week=today_day_of_week
        ).order_by('start_time')
        serializer = ReadingScheduleSerializer(schedules, many=True)
        return Response({"status": "success", "data": serializer.data})


class BookViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = BookSerializer

    def get_queryset(self):
        return Book.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class StartSessionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # Prevent starting a new session if one is already active
        active = ReadingSession.objects.filter(user=request.user, ended_at__isnull=True).first()
        if active:
            serializer = ReadingSessionSerializer(active)
            return Response({
                "status": "error",
                "message": "A session is already active.",
                "data": serializer.data
            }, status=status.HTTP_400_BAD_REQUEST)

        session_type = request.data.get('session_type')
        schedule_id = request.data.get('schedule_id')
        book_id = request.data.get('book_id')
        start_page = request.data.get('start_page')

        if session_type not in ['Career', 'Self-Dev']:
            return Response({
                "status": "error",
                "message": "Invalid session_type. Must be 'Career' or 'Self-Dev'."
            }, status=status.HTTP_400_BAD_REQUEST)

        schedule = None
        if schedule_id:
            try:
                schedule = ReadingSchedule.objects.get(id=schedule_id, user=request.user)
            except ReadingSchedule.DoesNotExist:
                pass

        book = None
        if book_id:
            try:
                book = Book.objects.get(id=book_id, user=request.user)
                if start_page is None:
                    start_page = book.current_page
            except Book.DoesNotExist:
                pass

        session = ReadingSession.objects.create(
            user=request.user,
            session_type=session_type,
            schedule=schedule,
            book=book,
            start_page=start_page
        )

        serializer = ReadingSessionSerializer(session)
        return Response({"status": "success", "data": serializer.data}, status=status.HTTP_201_CREATED)


class EndSessionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        active = ReadingSession.objects.filter(user=request.user, ended_at__isnull=True).first()
        if not active:
            return Response({
                "status": "error",
                "message": "No active session found."
            }, status=status.HTTP_404_NOT_FOUND)

        active.ended_at = timezone.now()
        active.notes = request.data.get('notes', '')
        end_page = request.data.get('end_page')
        
        if end_page:
            active.end_page = end_page
            if active.book:
                active.book.current_page = end_page
                if active.book.total_pages > 0 and end_page >= active.book.total_pages:
                    active.book.status = 'Completed'
                else:
                    active.book.status = 'Reading'
                active.book.save()
        
        active.save()

        serializer = ReadingSessionSerializer(active)
        return Response({"status": "success", "data": serializer.data})


class ActiveSessionView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        active = ReadingSession.objects.filter(user=request.user, ended_at__isnull=True).first()
        if active:
            serializer = ReadingSessionSerializer(active)
            return Response({"status": "success", "data": serializer.data})
        return Response({"status": "success", "data": None})


class DashboardSummaryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        now = timezone.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = today_start - timedelta(days=today_start.weekday())

        # Today's completed sessions
        today_sessions = ReadingSession.objects.filter(
            user=request.user,
            started_at__gte=today_start,
            ended_at__isnull=False
        )

        career_minutes_today = sum(
            s.duration_minutes for s in today_sessions if s.session_type == 'Career' and s.duration_minutes
        )
        self_dev_minutes_today = sum(
            s.duration_minutes for s in today_sessions if s.session_type == 'Self-Dev' and s.duration_minutes
        )

        # Weekly hours
        week_sessions = ReadingSession.objects.filter(
            user=request.user,
            started_at__gte=week_start,
            ended_at__isnull=False
        )
        weekly_minutes = sum(s.duration_minutes for s in week_sessions if s.duration_minutes)

        # Daily goal: weekday target is 2.5 + 1.5 = 4h = 240 min
        # Weekend target is 4 + 3.75 avg = 7.75h, just use 240 min daily for simplicity
        daily_target_minutes = 240
        total_today_minutes = career_minutes_today + self_dev_minutes_today
        daily_progress = min(round((total_today_minutes / daily_target_minutes) * 100), 100)

        # Streak: count consecutive days with at least one completed session
        streak = 0
        check_date = today_start
        while True:
            day_end = check_date + timedelta(days=1)
            has_session = ReadingSession.objects.filter(
                user=request.user,
                started_at__gte=check_date,
                started_at__lt=day_end,
                ended_at__isnull=False
            ).exists()
            if has_session:
                streak += 1
                check_date -= timedelta(days=1)
            else:
                break

        return Response({
            "status": "success",
            "data": {
                "daily_progress": daily_progress,
                "weekly_hours": round(weekly_minutes / 60, 1),
                "current_streak": streak,
                "career_hours_today": round(career_minutes_today / 60, 1),
                "self_dev_hours_today": round(self_dev_minutes_today / 60, 1),
            }
        })


class SessionHistoryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Return last 30 completed sessions
        sessions = ReadingSession.objects.filter(
            user=request.user,
            ended_at__isnull=False
        ).order_by('-started_at')[:30]
        serializer = ReadingSessionSerializer(sessions, many=True)
        return Response({"status": "success", "data": serializer.data})


class WeeklyAnalyticsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        now = timezone.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

        # Build 7-day breakdown starting from 6 weeks ago
        weeks_data = []
        DAY_NAMES = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']

        # Current week day-by-day chart data (last 7 days)
        daily_chart = []
        for i in range(6, -1, -1):
            day_start = today_start - timedelta(days=i)
            day_end = day_start + timedelta(days=1)
            day_sessions = ReadingSession.objects.filter(
                user=request.user,
                started_at__gte=day_start,
                started_at__lt=day_end,
                ended_at__isnull=False
            )
            career_mins = sum(s.duration_minutes for s in day_sessions if s.session_type == 'Career' and s.duration_minutes)
            self_dev_mins = sum(s.duration_minutes for s in day_sessions if s.session_type == 'Self-Dev' and s.duration_minutes)
            daily_chart.append({
                "day": DAY_NAMES[day_start.weekday()],
                "date": day_start.strftime('%b %d'),
                "career": round(career_mins / 60, 2),
                "self_dev": round(self_dev_mins / 60, 2),
                "total": round((career_mins + self_dev_mins) / 60, 2),
            })

        # Weekly totals for the past 8 weeks
        weekly_chart = []
        week_start = today_start - timedelta(days=today_start.weekday())
        for i in range(7, -1, -1):
            wk_start = week_start - timedelta(weeks=i)
            wk_end = wk_start + timedelta(weeks=1)
            wk_sessions = ReadingSession.objects.filter(
                user=request.user,
                started_at__gte=wk_start,
                started_at__lt=wk_end,
                ended_at__isnull=False
            )
            career_mins = sum(s.duration_minutes for s in wk_sessions if s.session_type == 'Career' and s.duration_minutes)
            self_dev_mins = sum(s.duration_minutes for s in wk_sessions if s.session_type == 'Self-Dev' and s.duration_minutes)
            weekly_chart.append({
                "week": f"Wk {wk_start.strftime('%b %d')}",
                "career": round(career_mins / 60, 1),
                "self_dev": round(self_dev_mins / 60, 1),
                "total": round((career_mins + self_dev_mins) / 60, 1),
            })

        # Overall totals
        all_sessions = ReadingSession.objects.filter(user=request.user, ended_at__isnull=False)
        total_career = sum(s.duration_minutes for s in all_sessions if s.session_type == 'Career' and s.duration_minutes)
        total_self_dev = sum(s.duration_minutes for s in all_sessions if s.session_type == 'Self-Dev' and s.duration_minutes)

        return Response({
            "status": "success",
            "data": {
                "daily_chart": daily_chart,
                "weekly_chart": weekly_chart,
                "total_career_hours": round(total_career / 60, 1),
                "total_self_dev_hours": round(total_self_dev / 60, 1),
                "total_sessions": all_sessions.count(),
            }
        })


class FullScheduleView(APIView):
    """GET full weekly schedule, POST to create a new schedule entry."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        schedules = ReadingSchedule.objects.filter(user=request.user)
        serializer = ReadingScheduleSerializer(schedules, many=True)
        return Response({"status": "success", "data": serializer.data})

    def post(self, request):
        serializer = ReadingScheduleSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response({"status": "success", "data": serializer.data}, status=status.HTTP_201_CREATED)
        return Response({"status": "error", "data": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class ScheduleDetailView(APIView):
    """PATCH to update, DELETE to remove a schedule entry."""
    permission_classes = [IsAuthenticated]

    def get_object(self, request, pk):
        try:
            return ReadingSchedule.objects.get(pk=pk, user=request.user)
        except ReadingSchedule.DoesNotExist:
            return None

    def patch(self, request, pk):
        obj = self.get_object(request, pk)
        if not obj:
            return Response({"status": "error", "message": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        serializer = ReadingScheduleSerializer(obj, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({"status": "success", "data": serializer.data})
        return Response({"status": "error", "data": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        obj = self.get_object(request, pk)
        if not obj:
            return Response({"status": "error", "message": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        obj.delete()
        return Response({"status": "success", "message": "Schedule entry deleted."}, status=status.HTTP_200_OK)


