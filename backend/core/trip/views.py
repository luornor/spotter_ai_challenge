from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import TripInputSerializer, TripPlanSerializer
from .services import plan_trip


class PlanTripView(APIView):
	def post(self, request):
		serializer = TripInputSerializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		plan = plan_trip(serializer.validated_data)
		out = TripPlanSerializer(plan)
		return Response(out.data, status=status.HTTP_200_OK)