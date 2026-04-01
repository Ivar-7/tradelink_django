import uuid
from decimal import Decimal
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet

from .models import Payment, PaymentStatus
from .serializers import PaymentSerializer, PaymentCreateSerializer, PaymentMethodSerializer


# In-memory storage for payment methods (replace with proper DB model later)
PAYMENT_METHODS = {}


class PaymentViewSet(ViewSet):
    """
    API for managing payments.
    
    Endpoints:
    - GET /payments/methods/ - List payment methods
    - POST /payments/methods/ - Create payment method
    - PATCH /payments/methods/{id}/default/ - Set default method
    - DELETE /payments/methods/{id}/ - Delete payment method
    - POST /payments/ - Create payment
    - GET /payments/{id}/verify/ - Verify payment status
    """
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'], url_path='methods', url_name='payment-methods-list')
    def list_methods(self, request):
        """GET /payments/methods/ - List user's payment methods."""
        user_id = str(request.user.id)
        methods = PAYMENT_METHODS.get(user_id, [])
        return Response({'methods': methods})

    @action(detail=False, methods=['post'], url_path='methods', url_name='payment-methods-create')
    def create_method(self, request):
        """POST /payments/methods/ - Create payment method."""
        serializer = PaymentMethodCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        card_number = serializer.validated_data['card_number'].replace(' ', '')
        method_id = str(uuid.uuid4())
        user_id = str(request.user.id)

        method = {
            'id': method_id,
            'brand': serializer.validated_data['brand'],
            'last4': card_number[-4:],
            'expiry_month': serializer.validated_data['expiry_month'],
            'expiry_year': serializer.validated_data['expiry_year'],
            'holder_name': serializer.validated_data['holder_name'],
            'is_default': not PAYMENT_METHODS.get(user_id),  # First method is default
        }

        if user_id not in PAYMENT_METHODS:
            PAYMENT_METHODS[user_id] = []
        
        PAYMENT_METHODS[user_id].append(method)

        return Response(method, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['delete'], url_path=r'methods/(?P<method_id>[^/.]+)', url_name='payment-methods-delete')
    def delete_method(self, request, method_id=None):
        """DELETE /payments/methods/{id}/ - Delete payment method."""
        user_id = str(request.user.id)
        methods = PAYMENT_METHODS.get(user_id, [])

        method_to_delete = None
        for method in methods:
            if method['id'] == method_id:
                method_to_delete = method
                break

        if not method_to_delete:
            return Response(
                {'detail': 'Payment method not found.'},
                status=status.HTTP_404_NOT_FOUND
            )

        methods.remove(method_to_delete)

        # If deleted was default, set first remaining as default
        if method_to_delete['is_default'] and methods:
            methods[0]['is_default'] = True

        return Response({'methods': methods})

    @action(detail=False, methods=['patch'], url_path=r'methods/(?P<method_id>[^/.]+)/default', url_name='payment-methods-set-default')
    def set_default(self, request, method_id=None):
        """PATCH /payments/methods/{id}/default/ - Set as default payment method."""
        user_id = str(request.user.id)
        methods = PAYMENT_METHODS.get(user_id, [])

        found = False
        for method in methods:
            if method['id'] == method_id:
                method['is_default'] = True
                found = True
            else:
                method['is_default'] = False

        if not found:
            return Response(
                {'detail': 'Payment method not found.'},
                status=status.HTTP_404_NOT_FOUND
            )

        return Response(
            next(m for m in methods if m['id'] == method_id),
            status=status.HTTP_200_OK
        )

    @action(detail=False, methods=['post'], url_path='', url_name='payment-create')
    def create_payment(self, request):
        """POST /payments/ - Create payment."""
        serializer = PaymentCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        payment = Payment.objects.create(
            user=request.user,
            order_id=int(serializer.validated_data['order_id']) if serializer.validated_data['order_id'].isdigit() else None,
            amount=serializer.validated_data['amount'],
            payment_provider=serializer.validated_data['payment_provider'],
            status=PaymentStatus.PENDING
        )

        # TODO: Integrate with actual payment processor (M-Pesa, Stripe, etc.)

        response_serializer = PaymentSerializer(payment)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'], url_path=r'(?P<payment_id>[^/.]+)/verify', url_name='payment-verify')
    def verify_payment(self, request, payment_id=None):
        """GET /payments/{id}/verify/ - Verify payment status."""
        try:
            payment = Payment.objects.get(id=payment_id, user=request.user)
        except Payment.DoesNotExist:
            return Response(
                {'detail': 'Payment not found.'},
                status=status.HTTP_404_NOT_FOUND
            )

        # TODO: Check with payment processor for actual status

        serializer = PaymentSerializer(payment)
        return Response(serializer.data)

