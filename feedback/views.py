from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Feedback
from .serializers import FeedbackSerializer, FeedbackCreateSerializer


class FeedbackView(APIView):
    """
    API for user feedback/contact form.
    
    Endpoints:
    - POST /feedback/ - Submit feedback
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """POST /feedback/ - Submit feedback."""
        serializer = FeedbackCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        feedback = Feedback.objects.create(
            user=request.user,
            type=serializer.validated_data['type'],
            message=serializer.validated_data['message']
        )

        response_serializer = FeedbackSerializer(feedback)
        return Response(
            {'success': True, 'item': response_serializer.data},
            status=status.HTTP_201_CREATED
        )

