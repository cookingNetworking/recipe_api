"""
Task for celery .
"""

from celery import shared_task
from celery.contrib.abortable import AbortableTask
from django.core.mail import send_mail
from celery import Celery

celery_app = Celery('app', broker='redis://cache:6379/1')

@shared_task(base=AbortableTask)
def delete_unactivate_user(user_email):
    from django.contrib.auth import get_user_model
    user = get_user_model().objects.filter(email=user_email).first()
    if  user and not user.is_active:
        user.delete()


@shared_task
def sending_mail(toemail, **content):
    """Function to send email . """
    try:
        send_mail(
        f"{content['subject']}",
        f"{content['message']}",
        "as2229181@gmail.com",
        [f"{toemail}"],
        fail_silently=False,
        )
        return
    except Exception as e:
        return e
