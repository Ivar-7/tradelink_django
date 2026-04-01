from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet

from products.models import Product
from .models import Review
from .serializers import ReviewSerializer, ReviewCreateSerializer, ReviewListSerializer


class ProductReviewViewSet(ViewSet):
    """
    API for managing product reviews.
    
    Endpoints:
    - GET /products/{productId}/reviews/ - List product reviews
    - POST /products/{productId}/reviews/ - Create review (authenticated)
    - DELETE /reviews/{id}/ - Delete review (authenticated, own)
    """
    permission_classes = [AllowAny]

    @action(detail=False, methods=['get'], url_path=r'products/(?P<product_id>[^/.]+)/reviews', url_name='product-reviews')
    def list_product_reviews(self, request, product_id=None):
        """GET /products/{productId}/reviews/ - List reviews for a product."""
        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return Response(
                {'detail': 'Product not found.'},
                status=status.HTTP_404_NOT_FOUND
            )

        reviews = product.reviews.all()
        average_rating = product.average_rating or 0.0

        serializer = ReviewSerializer(reviews, many=True)
        return Response({
            'reviews': serializer.data,
            'total': reviews.count(),
            'average_rating': average_rating
        })

    @action(detail=False, methods=['post'], url_path=r'products/(?P<product_id>[^/.]+)/reviews', url_name='create-review')
    def create_product_review(self, request, product_id=None):
        """POST /products/{productId}/reviews/ - Create a review."""
        if not request.user.is_authenticated:
            return Response(
                {'detail': 'Authentication required.'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return Response(
                {'detail': 'Product not found.'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Check if user already reviewed this product
        if Review.objects.filter(user=request.user, product=product).exists():
            return Response(
                {'detail': 'You have already reviewed this product.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = ReviewCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        review = Review.objects.create(
            user=request.user,
            product=product,
            rating_value=serializer.validated_data['rating_value'],
            comment=serializer.validated_data.get('comment', ''),
            verified_purchase=False  # Can be determined from order history
        )

        response_serializer = ReviewSerializer(review)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['delete'], url_path=r'reviews/(?P<review_id>[^/.]+)', url_name='delete-review')
    def delete_review(self, request, review_id=None):
        """DELETE /reviews/{id}/ - Delete a review."""
        try:
            review = Review.objects.get(id=review_id)
        except Review.DoesNotExist:
            return Response(
                {'detail': 'Review not found.'},
                status=status.HTTP_404_NOT_FOUND
            )

        if review.user != request.user and not request.user.is_staff:
            return Response(
                {'detail': 'You do not have permission to delete this review.'},
                status=status.HTTP_403_FORBIDDEN
            )

        review.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


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