from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import Utilisateur, Candidat, Recruteur, Offre, Entretien


class InscriptionForm(UserCreationForm):
    ROLE_CHOICES = [
        ('candidat', 'Candidat'),
        ('recruteur', 'Recruteur'),
    ]
    role = forms.ChoiceField(choices=ROLE_CHOICES, widget=forms.RadioSelect)
    nom = forms.CharField(max_length=100)
    prenom = forms.CharField(max_length=100)

    class Meta:
        model = Utilisateur
        fields = ('nom', 'prenom', 'email', 'password1', 'password2', 'role')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = self.cleaned_data['email']
        if commit:
            user.save()
            if user.role == 'candidat':
                Candidat.objects.create(utilisateur=user)
            elif user.role == 'recruteur':
                Recruteur.objects.create(utilisateur=user, entreprise="", telephone="", departement="")
        return user


class OffreForm(forms.ModelForm):
    class Meta:
        model = Offre
        fields = ['titre', 'description', 'lieu', 'type_contrat', 'date_expiration']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 6}),
            'date_expiration': forms.DateInput(attrs={'type': 'date'}),
        }


class CandidatureForm(forms.Form):
    cv = forms.FileField(label="Votre CV")
    lettre_motivation = forms.CharField(widget=forms.Textarea(attrs={'rows': 12}), label="Lettre de motivation")


class EntretienForm(forms.ModelForm):
    class Meta:
        model = Entretien
        fields = ['date', 'heure', 'lieu', 'type', 'notes']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'heure': forms.TimeInput(attrs={'type': 'time'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }


class ProfilCandidatForm(forms.Form):
    nom = forms.CharField(max_length=100)
    prenom = forms.CharField(max_length=100)
    telephone = forms.CharField(max_length=20, required=False)
    date_naissance = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))
    ville = forms.CharField(max_length=100, required=False)


class ProfilRecruteurForm(forms.Form):
    nom = forms.CharField(max_length=100)
    prenom = forms.CharField(max_length=100)
    entreprise = forms.CharField(max_length=200, required=False)
    telephone = forms.CharField(max_length=20, required=False)
    departement = forms.CharField(max_length=100, required=False)
