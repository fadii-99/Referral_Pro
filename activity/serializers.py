# activity/serializers.py
from rest_framework import serializers
from .models import ActivityLog

class ActivityLogSerializer(serializers.ModelSerializer):
    actor_name = serializers.SerializerMethodField()
    subject_name = serializers.SerializerMethodField()
    reference_id = serializers.SerializerMethodField()

    class Meta:
        model = ActivityLog
        fields = [
            "id","event","title","body","meta","created_at",
            "actor","actor_name","subject_user","subject_name",
            "referral","reference_id","chat_room","message"
        ]

    def get_actor_name(self, obj):
        return getattr(obj.actor, "full_name", None)

    def get_subject_name(self, obj):
        return getattr(obj.subject_user, "full_name", None)

    def get_reference_id(self, obj):
        return getattr(obj.referral, "reference_id", None)
