import boto3
import datetime
from botocore.config import Config
from storages.backends.s3boto3 import S3Boto3Storage

from django.contrib.auth import authenticate, login
from django.urls import reverse
from django.http import HttpResponse
from django.conf import settings
from django.shortcuts import render, redirect
from .forms import ImageUploadForm
from core.models import TestImageUpload
# Create your views here.
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes
from botocore.signers import CloudFrontSigner

def generate_presigned_url(bucket_name, object_name, expiration=3600):
    """Generate a presigned URL to share an S3 object."""
    s3_client = boto3.client('s3', aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                              aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
							  region_name=settings.AWS_S3_REGION_NAME,
							  config=Config(signature_version='s3v4')
							  )

    response = s3_client.generate_presigned_url('get_object',
                                                Params={'Bucket': bucket_name,
                                                        'Key': object_name},
                                                ExpiresIn=expiration)
    return response

def rsa_signer(message):
    """Hash the private key for singned cloudfront url!!"""
    private_key = serialization.load_pem_private_key(
        settings.AWS_CLOUDFRONT_KEY,
        password = None,
        backend=default_backend()
    )

    return private_key.sign(message, padding.PKCS1v15(), hashes.SHA256())

def create_signed_url(image_path):
    """
    Create signed url !
    Exprired time should be minutes !
    """
    url = f'https://{settings.AWS_S3_CUSTOM_DOMAIN}/{image_path}'
    expired_time = datetime.datetime.utcnow() + datetime.timedelta(minutes=30)
    print(expired_time)
    key_id = settings.AWS_CLOUDFRONT_KEY_ID
    cloudfront_signer = CloudFrontSigner(key_id, rsa_signer)
    print(key_id, type(key_id))
    signed_url = cloudfront_signer.generate_presigned_url(
                                                        url,
                                                        date_less_than=expired_time)
    return signed_url

def test_upload_image(request):
	"""Test upload image to aws s3."""
	s3_storage = S3Boto3Storage()
	if request.method == 'POST':
		form = ImageUploadForm(request.POST, request.FILES)
		if form.is_valid():
			form.save()
			return redirect('test:test_upload_image')
	else:
		presigned_urls = []
		form = ImageUploadForm()
		images = TestImageUpload.objects.filter().all()
		for image in images:
			print(image.image, type(image.image))
			url = s3_storage.url(str(image.image), expire=1800)
			presigned_urls.append((image.name,url))
		print(presigned_urls)
		return render(request, 'test_upload.html',{"form":form,"images":presigned_urls})

def notification_test_login(request):
    """Test page for notification, Login page!"""
    user = request.user
    if user.is_authenticated:
        return redirect(reverse('test:notification_notification'))
    else:
        if request.method == 'POST':
            email = request.POST['email']
            passowrd = request.POST['password']
            user = authenticate(request, username=email, password=passowrd)
            if user is not None:
                login(request, user)
                return redirect(reverse('test:notification_notification'))
        elif request.method == 'GET':
            return render(request, 'notification_test_login.html')
        else:
            return HttpResponse("405 Method not allowed")

def notification_notification(request):
    """Test create recipe for notification!"""
    user = request.user
    if user.is_authenticated:
        context = {}
        return render(request, 'index.html', context)
    else:
        return redirect(reverse('test:notification_test_login'))