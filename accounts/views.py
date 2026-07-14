from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.models import User

from .serializers import RegisterSerializer, UserSerializer, MeSerializer
from .models import Profile


class RegisterView(generics.CreateAPIView):
    """
    Register new user + auto create Profile.
    Returns user info + JWT tokens on success.
    """
    queryset = User.objects.all()
    permission_classes = [AllowAny]
    serializer_class = RegisterSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Generate tokens
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'user': UserSerializer(user).data,
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'message': 'ثبت‌نام با موفقیت انجام شد. خوش آمدید!'
        }, status=status.HTTP_201_CREATED)


class MeView(APIView):
    """
    Get current authenticated user's info + profile.
    Useful for frontend/app to fetch logged-in user data.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = MeSerializer(request.user)
        return Response(serializer.data)

    def patch(self, request):
        """Update profile fields"""
        profile = request.user.profile
        profile_data = request.data.get('profile', {})
        
        for field in ['telegram_chat_id', 'timezone', 'language', 'bio', 'avatar_url', 'preferences']:
            if field in profile_data:
                setattr(profile, field, profile_data[field])
        profile.save()
        
        return Response(MeSerializer(request.user).data)
