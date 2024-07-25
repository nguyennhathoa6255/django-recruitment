from django import forms

class TrackingForm(forms.Form):
    jd = forms.CharField(widget=forms.Textarea, required=True)
    resume = forms.FileField(required=True)

