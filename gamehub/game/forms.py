from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from . import logic


class SignUpForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username",)


class GuessForm(forms.Form):
    guess = forms.IntegerField(
        min_value=logic.MIN_NUMBER,
        max_value=logic.MAX_NUMBER,
        label=f"Your guess ({logic.MIN_NUMBER}-{logic.MAX_NUMBER})",
        widget=forms.NumberInput(attrs={"autofocus": True, "inputmode": "numeric"}),
        error_messages={
            "min_value": f"Pick a number from {logic.MIN_NUMBER} to {logic.MAX_NUMBER}.",
            "max_value": f"Pick a number from {logic.MIN_NUMBER} to {logic.MAX_NUMBER}.",
            "invalid": "Enter a whole number.",
        },
    )
