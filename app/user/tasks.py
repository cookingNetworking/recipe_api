from celery import shared_task



@shared_task
def delete_unactivate_user(user_email):
    from django.contrib.auth import get_user_model

    print(user_email)
    user = get_user_model().objects.filter(email=user_email).first()
    print(user)
    if  user and not user.is_active:
        user.delete()