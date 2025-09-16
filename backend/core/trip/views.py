# trip/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema
from .serializers import TripInputSerializer, TripPlanSerializer
from .services import plan_trip, TripPlanningError

@extend_schema(request=TripInputSerializer, responses={200: TripPlanSerializer}, tags=["trip"])
class PlanTripView(APIView):
    def post(self, request):
        s = TripInputSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        try:
            result = plan_trip(s.validated_data)
            return Response(TripPlanSerializer(result).data, status=status.HTTP_200_OK)
        except TripPlanningError as e:
            return Response({"detail": f"Trip planning error: {e}"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            # last-resort guard so the user never sees a 500
            return Response({"detail": f"Unexpected error: {e}"}, status=status.HTTP_400_BAD_REQUEST)
