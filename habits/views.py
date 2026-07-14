from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from datetime import date

from core.permissions import IsOwner
from .models import Habit, HabitLog
from .serializers import HabitSerializer, HabitLogSerializer


class HabitViewSet(viewsets.ModelViewSet):
    """
    Full CRUD for Habits + custom actions.
    Supports: list, create, retrieve, update, delete, log_today, stats
    """
    serializer_class = HabitSerializer
    permission_classes = [IsAuthenticated, IsOwner]
    filterset_fields = ['is_active', 'frequency']
    search_fields = ['name', 'description']
    ordering_fields = ['created_at', 'name']

    def get_queryset(self):
        return Habit.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'], url_path='log')
    def log_today(self, request, pk=None):
        """
        Quick log for today.
        POST /api/habits/{id}/log/   with {"completed": true, "count": 1, "notes": "..."}
        """
        habit = self.get_object()
        today = date.today()
        
        log, created = HabitLog.objects.get_or_create(
            habit=habit,
            date=today,
            defaults={
                'user': request.user,  # even if BaseModel, but HabitLog inherits
                'completed': request.data.get('completed', True),
                'count': request.data.get('count', 1),
                'notes': request.data.get('notes', '')
            }
        )
        
        if not created:
            # Update existing
            log.completed = request.data.get('completed', log.completed)
            log.count = request.data.get('count', log.count)
            if 'notes' in request.data:
                log.notes = request.data['notes']
            log.save()
        
        serializer = HabitLogSerializer(log)
        return Response({
            'message': 'عادت امروز ثبت شد.' if created else 'ثبت عادت به‌روزرسانی شد.',
            'log': serializer.data
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """
        Overall habits stats for dashboard.
        GET /api/habits/stats/
        """
        habits = self.get_queryset().filter(is_active=True)
        total_habits = habits.count()
        
        # Simple aggregate
        from django.db.models import Count
        logs_today = HabitLog.objects.filter(
            habit__user=request.user,
            date=date.today(),
            completed=True
        ).count()
        
        return Response({
            'total_active_habits': total_habits,
            'completed_today': logs_today,
            'message': 'آمار عادات فعال شما'
        })


class HabitLogViewSet(viewsets.ModelViewSet):
    """
    Separate ViewSet for logs if you want direct access / filtering by date etc.
    """
    serializer_class = HabitLogSerializer
    permission_classes = [IsAuthenticated, IsOwner]
    filterset_fields = ['date', 'completed', 'habit']
    ordering_fields = ['date', '-created_at']

    def get_queryset(self):
        return HabitLog.objects.filter(habit__user=self.request.user)

    def perform_create(self, serializer):
        habit = serializer.validated_data['habit']
        if habit.user != self.request.user:
            raise PermissionError("عادت متعلق به شما نیست")
        serializer.save(user=self.request.user)
