from rest_framework import serializers
from .models import Reminder


class ReminderSerializer(serializers.ModelSerializer):
    linked_object_type = serializers.SerializerMethodField()
    linked_object_repr = serializers.SerializerMethodField()
    
    class Meta:
        model = Reminder
        fields = [
            'id', 'title', 'description', 'remind_at', 'is_recurring',
            'recurrence_type', 'recurrence_interval', 'recurrence_end_date',
            'content_type', 'object_id', 'linked_object_type', 'linked_object_repr',
            'is_active', 'last_notified', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'last_notified', 'created_at', 'updated_at']

    def get_linked_object_type(self, obj):
        if obj.content_type:
            return obj.content_type.model
        return None

    def get_linked_object_repr(self, obj):
        if obj.content_object:
            return str(obj.content_object)[:100]
        return None
