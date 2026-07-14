from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import HabitViewSet, HabitLogViewSet

router = DefaultRouter()
router.register(r'', HabitViewSet, basename='habit')
router.register(r'logs', HabitLogViewSet, basename='habitlog')

urlpatterns = router.urls
