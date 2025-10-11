# views.py

from django.utils.dateparse import parse_datetime
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from datetime import datetime
from typing import Optional

from .models import ActivityLog
from accounts.models import User  # only needed if you keep 'mine' later


class ActivityListView(APIView):
    permission_classes = [IsAuthenticated]

    def _get_created_at(self, obj) -> Optional[str]:
        """
        Prefer obj.created_at; fall back to obj.timestamp; finally None.
        Always return ISO8601 string if present.
        """
        dt = None
        if hasattr(obj, "created_at") and isinstance(getattr(obj, "created_at"), datetime):
            dt = obj.created_at
        elif hasattr(obj, "timestamp") and isinstance(getattr(obj, "timestamp"), datetime):
            dt = obj.timestamp
        elif hasattr(obj, "updated_at") and isinstance(getattr(obj, "updated_at"), datetime):
            dt = obj.updated_at
        return dt.isoformat() if dt else None

    def _get_title(self, obj) -> Optional[str]:
        """
        Map common title-like fields to 'title'.
        """
        for name in ("title", "action", "event", "type", "name"):
            if hasattr(obj, name):
                val = getattr(obj, name)
                if val:
                    return str(val)
        return None

    def _get_body(self, obj) -> Optional[str]:
        """
        Map common body-like fields to 'body'.
        """
        for name in ("body", "message", "details", "description", "meta"):
            if hasattr(obj, name):
                val = getattr(obj, name)
                if val:
                    return val if isinstance(val, str) else str(val)
        return None

    def get(self, request):
        try:
            referral_id = request.query_params.get("referral_id")
            if not referral_id:
                return Response({"error": "referral_id is required"}, status=status.HTTP_400_BAD_REQUEST)

            qs = ActivityLog.objects.filter(referral_id=referral_id)

            # Optional since filter (?since=2025-10-01T00:00:00Z)
            since = request.query_params.get("since")
            if since:
                dt = parse_datetime(since)
                if dt:
                    if hasattr(ActivityLog, "created_at"):
                        qs = qs.filter(created_at__gte=dt)
                    elif hasattr(ActivityLog, "timestamp"):
                        qs = qs.filter(timestamp__gte=dt)

            # Ordering: prefer created_at, else timestamp, else id desc
            model_fields = {f.name for f in ActivityLog._meta.get_fields()}
            if "created_at" in model_fields:
                qs = qs.order_by("created_at")
            elif "timestamp" in model_fields:
                qs = qs.order_by("timestamp")
            else:
                qs = qs.order_by("id")

            results = []
            for obj in qs:
                results.append({
                    "id": getattr(obj, "id", None),
                    "created_at": self._get_created_at(obj),
                    "title": self._get_title(obj),
                    "body": self._get_body(obj),
                })

            return Response({"results": results}, status=status.HTTP_200_OK)

        except Exception as e:
            print("Error in ActivityListView:", str(e))
            return Response(
                {"error": "An error occurred while fetching activity logs."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
