# activity/views.py
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .models import ActivityLog
from .serializers import ActivityLogSerializer

class ActivityListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        referral_id = request.query_params.get("referral_id")
        mine = request.query_params.get("mine") in ("1","true","True")

        qs = ActivityLog.objects.all()
        if referral_id:
            qs = qs.filter(referral_id=referral_id)
        if mine:
            qs = qs.filter(actor=request.user)

        serializer = ActivityLogSerializer(qs[:200], many=True)  # cap it
        return Response({"results": serializer.data}, status=status.HTTP_200_OK)
