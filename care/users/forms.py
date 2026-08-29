from django import forms
from django.forms import ModelForm
from users.models import patient_insc, psy_insc, RDV, emp_auth

# === Formulaire Patient ===
class InscPatient(ModelForm):
    class Meta:
        model = patient_insc
        fields = ["Name", "my_email", "my_password", "passw", "Sexe", "NumTel"]
        labels = {
            'Name': 'Nom & Prénom',
            'my_email': 'Adresse e-mail',
            'my_password': 'Mot de passe',
            'passw': 'Confirmation de mot de passe',
            'Sexe': 'Sexe',
            'NumTel': 'Numéro de téléphone',
        }
        widgets = {
            'my_password': forms.PasswordInput(attrs={'class': 'form-control'}),
            'passw': forms.PasswordInput(attrs={'class': 'form-control'}),
        }


class InscPsy(ModelForm):
    class Meta:
        model = psy_insc
        fields = ["Name", "email", "password", "passw", "fichiers", "localisation_cabinet", "latitude", "longitude"]
        labels = {
            'Name': 'Nom & Prénom',
            'email': 'Adresse e-mail',
            'password': 'Mot de passe',
            'passw': 'Confirmation du mot de passe',
            'fichiers': 'Fichier à télécharger',
            'localisation_cabinet': 'Localisation du cabinet',
        }
        widgets = {
            'password': forms.PasswordInput(attrs={'class':'form-control'}),
            'passw': forms.PasswordInput(attrs={'class':'form-control'}),
            'latitude': forms.HiddenInput(),
            'longitude': forms.HiddenInput(),
        }


# === Formulaire Authentification ===
class AuthForm(ModelForm):
    class Meta:
        model = emp_auth
        fields = ["email", "password"]
        labels = {
            'email': 'Adresse email',
            'password': 'Mot de passe',
        }
        widgets = {
            'password': forms.PasswordInput(attrs={'class': 'form-control'}),
        }


# === Formulaire RDV ===
class RDV_form(ModelForm):
    class Meta:
        model = RDV
        fields = ['date', 'email']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }
        labels = {
            'date': '',
        }
