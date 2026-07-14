from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Sum
from decimal import Decimal
from datetime import date, timedelta

from core.permissions import IsOwner
from core.utils import get_finance_summary
from .models import Transaction, TransactionCategory
from .serializers import TransactionSerializer, TransactionCategorySerializer


class TransactionViewSet(viewsets.ModelViewSet):
    """
    CRUD Transactions + powerful summary endpoint for reports.
    """
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated, IsOwner]
    filterset_fields = ['type', 'category', 'date', 'payment_method']
    search_fields = ['description', 'notes']
    ordering_fields = ['date', '-created_at', 'amount']

    def get_queryset(self):
        return Transaction.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['get'])
    def summary(self, request):
        """
        Financial summary.
        Query params: ?period=month or week or all, ?start_date=YYYY-MM-DD&end_date=...
        GET /api/finance/transactions/summary/
        """
        qs = self.get_queryset()
        
        period = request.query_params.get('period', 'month')
        start = request.query_params.get('start_date')
        end = request.query_params.get('end_date')
        
        if start and end:
            qs = qs.filter(date__range=[start, end])
        elif period == 'month':
            today = date.today()
            start_of_month = today.replace(day=1)
            qs = qs.filter(date__gte=start_of_month)
        elif period == 'week':
            today = date.today()
            start_of_week = today - timedelta(days=today.weekday())
            qs = qs.filter(date__gte=start_of_week)
        
        summary = get_finance_summary(qs, period)
        
        # Breakdown by category
        by_category = qs.values('category__name').annotate(
            total=Sum('amount')
        ).order_by('-total')[:10]
        
        return Response({
            'summary': summary,
            'by_category': list(by_category),
            'period': period
        })

    @action(detail=False, methods=['get'])
    def categories(self, request):
        """List available categories for this user + defaults"""
        user_cats = TransactionCategory.objects.filter(user=request.user)
        defaults = TransactionCategory.objects.filter(is_default=True, user__isnull=True)
        all_cats = (user_cats | defaults).distinct()
        return Response(TransactionCategorySerializer(all_cats, many=True).data)
