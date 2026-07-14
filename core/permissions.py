from rest_framework import permissions


class IsOwner(permissions.BasePermission):
    """
    Custom permission: Only owners of the object can view/edit/delete it.
    Works with models that have .user attribute or related (e.g. HabitLog -> habit.user)
    """
    message = "شما مالک این مورد نیستید."

    def has_object_permission(self, request, view, obj):
        # Direct user ownership
        if hasattr(obj, 'user'):
            return obj.user == request.user
        
        # For logs or related models (HabitLog, etc.)
        if hasattr(obj, 'habit') and hasattr(obj.habit, 'user'):
            return obj.habit.user == request.user
        
        if hasattr(obj, 'todo') and hasattr(obj.todo, 'user'):
            return obj.todo.user == request.user
        
        return False
