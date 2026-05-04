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

    # check if user has a valid JWT token
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """POST /feedback/ - Submit feedback."""

        # get data from JSON request body and pass to serializer to check for validity
        serializer = FeedbackCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # call supabase service to save feedback to database
        feedback = FeedbackService.create_feedback(
            {
                "user_id": str(request.user.id),
                "type": serializer.validated_data["type"],
                "message": serializer.validated_data["message"],
            }
        )

        # create response object with feedback data
        return Response(
            {
                "success": True,
                "item": {
                    "id": feedback.get("feedback_id"),
                    "user_id": feedback.get("user_id"),
                    "type": feedback.get("type"),
                    "message": feedback.get("message"),
                    "created_at": feedback.get("date_submitted"),
                },
            },
            status=status.HTTP_201_CREATED,
        )
