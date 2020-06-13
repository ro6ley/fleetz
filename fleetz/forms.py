from django import forms
from django.contrib.auth.models import User
from django.contrib.postgres.forms import SimpleArrayField

from .models import FleetzUser


class ProfileForm(forms.ModelForm):
    triggers = SimpleArrayField(forms.CharField(), delimiter='|')

    class Meta:
        model = FleetzUser
        fields = ('hours', 'minutes')
