import logging

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny

from .services import Products

logger = logging.getLogger(__name__)


class ReviewView(APIView):
    """Handle CRUD operations for reviews."""

    permission_classes = [AllowAny]

    def get(self, request, pk=None):
        """
        Retrieve one review (by product_id) or list all reviews.
        """
        try:
            if pk:
                review = Products.get_review(pk)

                if not review:
                    return Response(
                        {"detail": "Review not found"},
                        status=status.HTTP_404_NOT_FOUND
                    )

                return Response(review)

            reviews = Products.list_reviews()
            return Response(reviews)

        except Exception as e:
            logger.error(f"Error retrieving reviews: {e}")
            return Response(
                {"detail": "Failed to retrieve reviews"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def post(self, request):
        """
        Create a new review.
        """
        try:
            product_id = request.data.get("product_id")
            user_id = request.data.get("user_id")
            rating_value = request.data.get("rating_value")
            comment = request.data.get("comment")

            if not product_id or not user_id or rating_value is None:
                return Response(
                    {"detail": "product_id, user_id and rating_value are required"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            review = Products.create_review(
                product_id=product_id,
                user_id=user_id,
                rating_value=rating_value,
                comment=comment
            )

            return Response(review, status=status.HTTP_201_CREATED)

        except Exception as e:
            logger.error(f"Error creating review: {e}")
            return Response(
                {"detail": "Failed to create review"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def put(self, request, pk):
        """
        Fully update a review.
        """
        try:
            user_id = request.data.get("user_id")
            rating_value = request.data.get("rating_value")
            comment = request.data.get("comment")

            if not user_id or rating_value is None:
                return Response(
                    {"detail": "user_id and rating_value are required"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            review = Products.update_review(
                product_id=pk,
                user_id=user_id,
                rating_value=rating_value,
                comment=comment
            )

            return Response(review)

        except Exception as e:
            logger.error(f"Error updating review: {e}")
            return Response(
                {"detail": "Failed to update review"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def patch(self, request, pk):
        """
        Partially update a review.
        """
        try:
            data = request.data

            if not data:
                return Response(
                    {"detail": "No data provided for update"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            review = Products.partial_update_review(pk, data)

            return Response(review)

        except Exception as e:
            logger.error(f"Error patching review: {e}")
            return Response(
                {"detail": "Failed to update review"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def delete(self, request, pk):
        """
        Delete a review.
        """
        try:
            success = Products.delete_review(pk)

            if not success:
                return Response(
                    {"detail": "Review not found"},
                    status=status.HTTP_404_NOT_FOUND
                )

            return Response(status=status.HTTP_204_NO_CONTENT)

        except Exception as e:
            logger.error(f"Error deleting review: {e}")
            return Response(
                {"detail": "Failed to delete review"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )