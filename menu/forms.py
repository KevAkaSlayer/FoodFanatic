from django import forms
from .models import Review
<<<<<<< HEAD
# class ReviewForm(forms.Form):
#     review = forms.CharField(widget=forms.Textarea)

class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields=['body','rating']
=======

class ReviewForm(forms.ModelForm):
    class Meta :
        model = Review
        fields = ['body','rating']
>>>>>>> refs/remotes/origin/main
