from rest_framework import serializers
from .models import Habit, HabitLog
from core.utils import calculate_current_streak


class HabitLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = HabitLog
        fields = [
            'id', 'habit', 'date', 'completed', 'count', 'notes', 
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate(self, data):
        # Ensure habit belongs to current user (extra safety)
        request = self.context.get('request')
        if request and data.get('habit'):
            if data['habit'].user != request.user:
                raise serializers.ValidationError("عادت متعلق به شما نیست.")
        return data


class HabitSerializer(serializers.ModelSerializer):
    logs = HabitLogSerializer(many=True, read_only=True)
    current_streak = serializers.SerializerMethodField()
    completion_rate_30d = serializers.SerializerMethodField()
    
    class Meta:
        model = Habit
        fields = [
            'id', 'name', 'description', 'frequency', 'target_per_period', 
            'period_days', 'color', 'icon', 'is_active',
            'created_at', 'updated_at', 'logs', 
            'current_streak', 'completion_rate_30d'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'user']

    def get_current_streak(self, obj):
        # Get recent log dates where completed=True
        log_dates = obj.logs.filter(completed=True).values_list('date', flat=True)
        return calculate_current_streak(list(log_dates))

    def get_completion_rate_30d(self, obj):
        from core.utils import calculate_completion_rate
        return calculate_completion_rate(obj.logs.all(), days=30)

    def create(self, validated_data):
        # user set in view
        return super().create(validated_data)
