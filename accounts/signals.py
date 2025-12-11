from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.forms.models import model_to_dict
from django.core.serializers.json import DjangoJSONEncoder
from .models import Log, Session
from accounts.middleware import get_current_user, get_current_ip
import json
from django.utils.timezone import now
from django.db import transaction
from accounts.models import Connection

@receiver(post_save)
def log_create_update(sender, instance, created, **kwargs):
    if sender.__name__ == 'Log':
        return

    user = get_current_user()
    ip = get_current_ip()

    if user and getattr(user, 'is_authenticated', False):
        object_id = getattr(instance, 'pk', None)
        if object_id is None:
            return

        try:
            changes = json.dumps(model_to_dict(instance), cls=DjangoJSONEncoder)
        except Exception:
            changes = None

        Log.objects.create(
            model_name=sender.__name__,
            object_id=str(object_id),
            action='create' if created else 'update',
            changes=changes,
            triggered_by=user,
            ip_address=ip
        )


@receiver(post_delete)
def log_delete(sender, instance, **kwargs):
    if sender.__name__ == 'Log':
        return

    user = get_current_user()
    ip = get_current_ip()

    if user and getattr(user, 'is_authenticated', False):
        object_id = getattr(instance, 'pk', None)
        if object_id is None:
            return

        Log.objects.create(
            model_name=sender.__name__,
            object_id=str(object_id),
            action='delete',
            changes=None,
            triggered_by=user,
            ip_address=ip
        )

@receiver(post_save, sender=Session)
def log_session_create(sender, instance, created, **kwargs):
    if created:
        user = instance.user
        Log.objects.create(
            model_name='Session',
            object_id=str(instance.pk),
            action='create',
            changes=None,
            triggered_by=user,
            timestamp=now(),
            ip_address=instance.ip
        )
