from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet
from drf_spectacular.utils import extend_schema

from products.services import ProductService
from .serializers import ReviewCreateSerializer
from .services import ReviewService


class ProductReviewViewSet(ViewSet):
    """
    API for managing product reviews.

    Endpoints:
    - GET /products/{productId}/reviews/ - List product reviews
    - POST /products/{productId}/reviews/ - Create review (authenticated)
    - DELETE /reviews/{id}/ - Delete review (authenticated, own)
    """

    permission_classes = [AllowAny]

    REVIEW_RESPONSES = {}

    @staticmethod
    def _normalize(item):
        return {
            "id": item.get("review_id"),
            "user_id": item.get("user_id"),
            "username": item.get("username", ""),
            "product_id": item.get("product_id"),
            "rating_value": item.get("rating_value"),
            "comment": item.get("comment", ""),
            "verified_purchase": item.get("verified_purchase", False),
            "helpful_count": item.get("helpful_count", 0),
            "date": item.get("date_created"),
        }

    # endpoint for getting reviews for a product
    @action(
        detail=False,
        methods=["get"],
        url_path=r"products/(?P<product_id>[^/.]+)/reviews",
        url_name="product-reviews",
    )
    def list_product_reviews(self, request, product_id=None):

        # check if product exists
        product = ProductService.get_product(product_id)
        if not product:
            return Response(
                {"detail": "Product not found."}, status=status.HTTP_404_NOT_FOUND
            )

        reviews = [
            self._normalize(review)
            for review in ReviewService.list_reviews()
            if review.get("product_id") == product_id
        ]

        avg = 0.0
        if reviews:
            avg = round(
                sum(float(r.get("rating_value") or 0) for r in reviews) / len(reviews),
                2,
            )

        return Response(
            {"reviews": reviews, "total": len(reviews), "average_rating": avg}
        )

    @extend_schema(operation_id="v1_reviews_list")
    def list(self, request):
        reviews = [self._normalize(review) for review in ReviewService.list_reviews()]
        return Response({"reviews": reviews, "total": len(reviews)})

    @extend_schema(operation_id="v1_reviews_product")
    def retrieve(self, request, pk=None):
        product = ProductService.get_product(pk)
        if not product:
            return Response(
                {"detail": "Product not found."}, status=status.HTTP_404_NOT_FOUND
            )
        reviews = [
            self._normalize(review)
            for review in ReviewService.list_reviews()
            if review.get("product_id") == pk
        ]
        return Response({"product_id": pk, "reviews": reviews, "total": len(reviews)})

    # endpoint for posting review
    @action(
        detail=False,
        methods=["post"],
        url_path=r"products/(?P<product_id>[^/.]+)/reviews",
        url_name="create-review",
    )
    def create_product_review(self, request, product_id=None):
        if not request.user.is_authenticated:
            return Response(
                {"detail": "Authentication required."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        # check if product exists
        product = ProductService.get_product(product_id)
        if not product:
            return Response(
                {"detail": "Product not found."}, status=status.HTTP_404_NOT_FOUND
            )

        # only one review per user per product
        user_id = str(request.user.id)
        existing = [
            r
            for r in ReviewService.list_reviews()
            if r.get("product_id") == product_id and r.get("user_id") == user_id
        ]
        if existing:
            return Response(
                {"detail": "You have already reviewed this product."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = ReviewCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        review = ReviewService.create_review(
            product_id=product_id,
            user_id=user_id,
            rating_value=serializer.validated_data["rating_value"],
            comment=serializer.validated_data.get("comment", ""),
        )

        return Response(self._normalize(review), status=status.HTTP_201_CREATED)

    @action(
        detail=False,
        methods=["delete"],
        url_path=r"reviews/(?P<review_id>[^/.]+)",
        url_name="delete-review",
    )
    def delete_review(self, request, review_id=None):
        reviews = ReviewService.list_reviews()
        target = next((r for r in reviews if r.get("review_id") == review_id), None)
        if not target:
            return Response(
                {"detail": "Review not found."}, status=status.HTTP_404_NOT_FOUND
            )

        if not request.user.is_authenticated:
            return Response(
                {"detail": "Authentication required."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if target.get("user_id") != str(request.user.id) and not request.user.is_staff:
            return Response(
                {"detail": "You do not have permission to delete this review."},
                status=status.HTTP_403_FORBIDDEN,
            )

        ReviewService.delete_review(review_id)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["post"], url_path="respond")
    def respond(self, request, pk=None):
        if not request.user.is_authenticated:
            return Response(
                {"detail": "Authentication required."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        response_text = request.data.get("response")
        if not response_text:
            return Response(
                {"detail": "response is required."}, status=status.HTTP_400_BAD_REQUEST
            )

        review = ReviewService.get_review(pk)
        if not review:
            return Response(
                {"detail": "Review not found."}, status=status.HTTP_404_NOT_FOUND
            )

        self.REVIEW_RESPONSES[str(pk)] = {
            "review_id": pk,
            "response": response_text,
            "responder_id": str(request.user.id),
        }

        return Response(self.REVIEW_RESPONSES[str(pk)], status=status.HTTP_201_CREATED)
