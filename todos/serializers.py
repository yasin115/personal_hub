from rest_framework import serializers
from .models import Todo


class TodoSerializer(serializers.ModelSerializer):
    subtasks = serializers.SerializerMethodField()
    
    class Meta:
        model = Todo
        fields = [
            'id', 'title', 'description', 'due_date', 'priority', 'status',
            'completed_at', 'parent', 'order', 'created_at', 'updated_at',
            'subtasks'
        ]
        read_only_fields = ['id', 'completed_at', 'created_at', 'updated_at']

    def get_subtasks(self, obj):
        if obj.subtasks.exists():
            return TodoSerializer(obj.subtasks.all(), many=True, context=self.context).data
        return []

    def validate_parent(self, value):
        if value and value.user != self.context['request'].user:
            raise serializers.ValidationError("والد متعلق به شما نیست.")
        return value
