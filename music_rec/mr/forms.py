from django import forms


class TrackForm(forms.Form):
    # like = forms.NullBooleanField(help_text="Like")
    # dislike = forms.NullBooleanField(help_text="Dislike")
    # skip = forms.NullBooleanField(help_text="Skip")
    # listen_through = forms.NullBooleanField(help_text="Listen through")
    # ignore = forms.NullBooleanField(help_text="ignore")

    like = forms.CharField(empty_value=None)
    dislike = forms.CharField(empty_value=None)
    skip = forms.CharField(empty_value=None)
    listen_through = forms.CharField(empty_value=None)
    ignore = forms.CharField(empty_value=None)
