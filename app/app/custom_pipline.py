"""
Customerize the django social pipline
"""
from social_core.exceptions import AuthAlreadyAssociated
from django.contrib.auth import logout, get_user_model


def set_user_active(backend, user, response, *args, **kwargs):
	"""
	After create user instacne using google oauth 2.0, activate user !
	"""
	user.is_active = True
	user.save()
	return kwargs
