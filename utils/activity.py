# utils/activity.py
import json
from typing import Optional, Dict, Any
from django.db import transaction
from activity.models import ActivityLog

def log_activity(
    *,
    event: str,
    actor=None,
    referral=None,
    title: str = "",
    body: str = "",
    subject_user=None,
    chat_room=None,
    message=None,
    meta: Optional[Dict[str, Any]] = None,
):
    # If you're not on Postgres JSONField, serialize meta here:
    # if meta is not None and not isinstance(meta, str):
    #     meta = json.dumps(meta, ensure_ascii=False)

    with transaction.atomic():
        ActivityLog.objects.create(
            event=event,
            actor=actor,
            referral=referral,
            title=title[:200] if title else "",
            body=body or "",
            subject_user=subject_user,
            chat_room=chat_room,
            message=message,
            meta=meta or {},
        )
