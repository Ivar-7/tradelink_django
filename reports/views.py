from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from . import services, serializers

class SalesReportView(APIView):
    def get(self, request):
        serializer = serializers.SalesFilterSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        
        vendor_id = request.user.vendor_profile.vendor_id  # however you resolve it
        data = services.SalesService.get_overview(
            vendor_id=vendor_id,
            **serializer.validated_data
        )
        return Response(data)

class OrdersReportView(APIView):
    def get(self, request):
        serializer = serializers.OrdersFilterSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        
        vendor_id = request.user.vendor_profile.vendor_id
        data = services.OrdersService.get_report(
            vendor_id=vendor_id,
            **serializer.validated_data
        )
        return Response(data)

class ProductsReportView(APIView):
    def get(self, request):
        serializer = serializers.ProductsFilterSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        
        vendor_id = request.user.vendor_profile.vendor_id
        data = services.ProductsService.get_report(
            vendor_id=vendor_id,
            **serializer.validated_data
        )
        return Response(data)

# --- Stubs for the not-yet-connected reports ---
class InventoryReportView(APIView):
    def get(self, request):
        return Response({"detail": "Inventory API not yet connected"}, status=501)

class MovementsReportView(APIView):
    def get(self, request):
        return Response({"detail": "Movements API not yet connected"}, status=501)

class EarningsReportView(APIView):
    def get(self, request):
        return Response({"detail": "Wallet API not yet connected"}, status=501)

class PayoutsReportView(APIView):
    def get(self, request):
        return Response({"detail": "Payouts API not yet connected"}, status=501)

class ReviewsReportView(APIView):
    def get(self, request):
        return Response({"detail": "Reviews API not yet connected"}, status=501)

class ShipmentsReportView(APIView):
    def get(self, request):
        return Response({"detail": "Shipments API not yet connected"}, status=501)

class SubordersReportView(APIView):
    def get(self, request):
        return Response({"detail": "Suborders API not yet connected"}, status=501)