from datetime import date, timedelta
from django.utils import timezone
from collections import defaultdict


def calculate_current_streak(log_dates):
    """
    Calculate current streak from a list of date objects (sorted descending preferably).
    Assumes daily habits. For weekly etc. adjust logic.
    log_dates: list of date objects where action happened.
    Returns: int (current streak days)
    """
    if not log_dates:
        return 0
    
    # Ensure sorted descending (most recent first)
    sorted_dates = sorted(set(log_dates), reverse=True)
    
    today = date.today()
    streak = 0
    current_date = today
    
    for log_date in sorted_dates:
        if log_date == current_date:
            streak += 1
            current_date -= timedelta(days=1)
        elif log_date < current_date:
            # Gap found
            break
        # if log_date > current_date: ignore future? shouldn't happen
    
    return streak


def calculate_completion_rate(logs_queryset, days=30):
    """
    Simple completion rate over last N days.
    logs_queryset: HabitLog queryset filtered for a habit.
    Returns: float percentage (0-100)
    """
    from datetime import date
    end = date.today()
    start = end - timedelta(days=days)
    
    total_days = days
    completed_days = logs_queryset.filter(
        date__range=(start, end),
        completed=True
    ).count()
    
    # For simplicity assume target 1 per day. For multiple targets adjust.
    rate = (completed_days / total_days) * 100 if total_days > 0 else 0
    return round(rate, 1)


def get_finance_summary(transactions_qs, period='month'):
    """
    Aggregate income vs expense.
    transactions_qs: Transaction queryset for user.
    Returns dict with totals.
    """
    from django.db.models import Sum, Q
    from decimal import Decimal
    
    if period == 'month':
        # You can enhance with date filters outside
        pass
    
    income = transactions_qs.filter(type='income').aggregate(
        total=Sum('amount')
    )['total'] or Decimal('0')
    
    expense = transactions_qs.filter(type='expense').aggregate(
        total=Sum('amount')
    )['total'] or Decimal('0')
    
    return {
        'total_income': float(income),
        'total_expense': float(expense),
        'balance': float(income - expense),
        'count': transactions_qs.count()
    }
