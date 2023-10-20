import boto3
from botocore.config import Config

from django.conf import settings
from django.shortcuts import render, redirect
from .forms import ImageUploadForm
from core.models import TestImageUpload
# Create your views here.


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

def test_upload_image(request):
	"""Test upload image to aws s3."""
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
			url = generate_presigned_url(settings.AWS_STORAGE_BUCKET_NAME, image.image.name)
			presigned_urls.append((image.name,url))	
		print(presigned_urls)
		return render(request, 'test_upload.html',{"form":form,"images":presigned_urls})