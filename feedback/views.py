from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import FeedbackCreateSerializer
from .services import FeedbackService


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

        feedback = FeedbackService.create_feedback(
            {
                'user_id': str(request.user.id),
                'type': serializer.validated_data['type'],
                'message': serializer.validated_data['message'],
            }
        )

        return Response(
            {
                'success': True,
                'item': {
                    'id': feedback.get('feedback_id'),
                    'user_id': feedback.get('user_id'),
                    'type': feedback.get('type'),
                    'message': feedback.get('message'),
                    'created_at': feedback.get('date_submitted'),
                },
            },
            status=status.HTTP_201_CREATED
        )

