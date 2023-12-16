"""Use for test """


from django import forms
from core.models import TestImageUpload

class ImageUploadForm(forms.ModelForm):
    """Use for test upload form!"""
    class Meta:
        model = TestImageUpload
        fields = ('name','image')
