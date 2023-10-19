from django.shortcuts import render
from .forms import ImageUploadForm
# Create your views here.


def test_upload_image(request):
	"""Test upload image to aws s3."""
	if request.method == 'POST':
		form = ImageUploadForm(request.POST, request.FILES)
		if form.is_valid():
			form.save()
			imj_object = form.instance
			return render(request, 'test_upload.html',{"from":form,"imj_object":imj_object})
	else:
		form = ImageUploadForm()
		return render(request, 'test_upload.html',{"form":form})