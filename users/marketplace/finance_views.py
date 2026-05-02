from decimal import Decimal

from drf_spectacular.utils import extend_schema
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from payments.services import PaymentService


class PayoutsView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(operation_id="v1_payouts_list")
    def get(self, request):
        payments = PaymentService.list_payments(str(request.user.id))
        payouts = []
        for payment in payments:
            amount = Decimal(str(payment.get("amount") or 0)) * Decimal("0.9")
            payouts.append(
                {
                    "id": f"payout-{payment.get('payment_id')}",
                    "payment_id": payment.get("payment_id"),
                    "amount": float(amount),
                    "status": "processed" if payment.get("status") == "completed" else "pending",
                    "created_at": payment.get("created_at"),
                }
            )
        return Response({"payouts": payouts, "total": len(payouts)})


class PayoutDetailView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(operation_id="v1_payouts_detail")
    def get(self, request, payout_id):
        payments = PaymentService.list_payments(str(request.user.id))
        for payment in payments:
            if f"payout-{payment.get('payment_id')}" == payout_id:
                amount = Decimal(str(payment.get("amount") or 0)) * Decimal("0.9")
                return Response(
                    {
                        "id": payout_id,
                        "payment_id": payment.get("payment_id"),
                        "amount": float(amount),
                        "status": "processed" if payment.get("status") == "completed" else "pending",
                        "created_at": payment.get("created_at"),
                    }
                )
        return Response({"detail": "Payout not found."}, status=404)


class WalletView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        payments = PaymentService.list_payments(str(request.user.id))
        available = Decimal("0")
        pending = Decimal("0")
        for payment in payments:
            value = Decimal(str(payment.get("amount") or 0)) * Decimal("0.9")
            if payment.get("status") == "completed":
                available += value
            else:
                pending += value
        return Response({"currency": "KES", "available": float(available), "pending": float(pending)})
