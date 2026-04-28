from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    TodayScheduleView,
    DashboardSummaryView,
    StartSessionView,
    EndSessionView,
    ActiveSessionView,
    SessionHistoryView,
    WeeklyAnalyticsView,
    FullScheduleView,
    ScheduleDetailView,
    BookViewSet,
)

router = DefaultRouter()
router.register(r'books', BookViewSet, basename='book')

urlpatterns = [
    path('', include(router.urls)),
    path('schedule/today/', TodayScheduleView.as_view(), name='schedule-today'),
    path('schedule/', FullScheduleView.as_view(), name='schedule-full'),
    path('schedule/<int:pk>/', ScheduleDetailView.as_view(), name='schedule-detail'),
    path('dashboard/summary/', DashboardSummaryView.as_view(), name='dashboard-summary'),
    path('sessions/start/', StartSessionView.as_view(), name='session-start'),
    path('sessions/end/', EndSessionView.as_view(), name='session-end'),
    path('sessions/active/', ActiveSessionView.as_view(), name='session-active'),
    path('sessions/history/', SessionHistoryView.as_view(), name='session-history'),
    path('analytics/weekly/', WeeklyAnalyticsView.as_view(), name='weekly-analytics'),
]
