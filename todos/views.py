from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone

from core.permissions import IsOwner
from .models import Todo
from .serializers import TodoSerializer


class TodoViewSet(viewsets.ModelViewSet):
    """
    Full CRUD + actions for Todos.
    Supports subtasks, status change, overdue filter etc.
    """
    serializer_class = TodoSerializer
    permission_classes = [IsAuthenticated, IsOwner]
    filterset_fields = ['status', 'priority', 'parent']
    search_fields = ['title', 'description']
    ordering_fields = ['order', 'due_date', '-created_at']

    def get_queryset(self):
        qs = Todo.objects.filter(user=self.request.user)
        # Optional: show only root tasks or all
        if self.request.query_params.get('root_only') == 'true':
            qs = qs.filter(parent__isnull=True)
        return qs

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'])
    def change_status(self, request, pk=None):
        todo = self.get_object()
        new_status = request.data.get('status')
        if new_status not in dict(Todo.STATUS_CHOICES):
            return Response({'error': 'وضعیت نامعتبر'}, status=400)
        
        todo.status = new_status
        if new_status == 'completed':
            todo.completed_at = timezone.now()
        todo.save()
        return Response(TodoSerializer(todo).data)

    @action(detail=False, methods=['get'])
    def overdue(self, request):
        from django.utils import timezone
        todos = self.get_queryset().filter(
            due_date__lt=timezone.now(),
            status__in=['pending', 'in_progress']
        )
        return Response(TodoSerializer(todos, many=True).data)
