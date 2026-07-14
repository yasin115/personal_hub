from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from datetime import timedelta

from core.permissions import IsOwner
from .models import Reminder
from .serializers import ReminderSerializer


class ReminderViewSet(viewsets.ModelViewSet):
    """
    CRUD for reminders + upcoming + mark notified.
    Extensible via GenericForeignKey.
    """
    serializer_class = ReminderSerializer
    permission_classes = [IsAuthenticated, IsOwner]
    filterset_fields = ['is_active', 'is_recurring', 'recurrence_type']
    ordering_fields = ['remind_at', '-created_at']

    def get_queryset(self):
        return Reminder.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['get'])
    def upcoming(self, request):
        """
        Get reminders due in next 24-48 hours.
        GET /api/reminders/upcoming/
        """
        now = timezone.now()
        soon = now + timedelta(hours=48)
        reminders = self.get_queryset().filter(
            remind_at__gte=now,
            remind_at__lte=soon,
            is_active=True
        ).order_by('remind_at')[:20]
        return Response(ReminderSerializer(reminders, many=True).data)

    @action(detail=True, methods=['post'])
    def mark_notified(self, request, pk=None):
        reminder = self.get_object()
        reminder.last_notified = timezone.now()
        if not reminder.is_recurring:
            reminder.is_active = False
        reminder.save()
        return Response({'message': 'یادآور به عنوان ارسال شده علامت خورد.'})
