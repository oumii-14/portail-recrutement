from django.db import models
from django.contrib.auth.models import AbstractUser



class Utilisateur(AbstractUser):
    ROLE_CHOICES = [
        ('candidat', 'Candidat'),
        ('recruteur', 'Recruteur'),
        ('admin', 'Administrateur'),
    ]
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    motDePasse = models.CharField(max_length=128)  
    dateCreation = models.DateTimeField(auto_now_add=True)
    statut = models.CharField(max_length=50, default='actif')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='candidat')

    def seConnecter(self) -> bool:
        return True

    def seDeconnecter(self) -> None:
        pass

    def modifierProfil(self) -> None:
        self.save()

    def __str__(self):
        return f"{self.prenom} {self.nom}"  'li kayt afficha 3nd l admin'



class Recruteur(models.Model):
    utilisateur = models.OneToOneField(Utilisateur, on_delete=models.CASCADE, related_name='recruteur_profil')
    entreprise = models.CharField(max_length=200)
    telephone = models.CharField(max_length=20)
    departement = models.CharField(max_length=100)

    def creerOffre(self):
        return Offre(recruteur=self)

    def modifierOffre(self, offre):
        offre.save()

    def supprimerOffre(self, offre):
        offre.delete()

    def consulterCandidatures(self):
        return Candidature.objects.filter(offre__recruteur=self) 
    def filterCandidatures(self):
        return self.consulterCandidatures()

    def accepterCandidature(self, candidature):
        statut = StatutCandidature.objects.get(nom="acceptee")
        candidature.statut = statut
        candidature.save()

    def rejeterCandidature(self, candidature):
        statut = StatutCandidature.objects.get(nom="rejetee")
        candidature.statut = statut
        candidature.save()

    def planifierEntretien(self):
        return Entretien()

    def envoyerMessage(self, destinataire):
        return Message(expediteur=self.utilisateur, destinataire=destinataire)

    def __str__(self):
        return self.utilisateur.username


class Candidat(models.Model):
    utilisateur = models.OneToOneField(Utilisateur, on_delete=models.CASCADE, related_name='candidat_profil')
    cv = models.FileField(upload_to='cv/', blank=True, null=True)
    profil = models.TextField(blank=True)
    telephone = models.CharField(max_length=20, blank=True)

    def __str__(self):
        return self.utilisateur.username



class Offre(models.Model):
    CONTRAT_CHOICES = [
        ('CDI', 'CDI'),
        ('CDD', 'CDD'),
        ('Stage', 'Stage'),
        ('Alternance', 'Alternance'),
    ]

    titre = models.CharField(max_length=200)
    description = models.TextField()
    lieu = models.CharField(max_length=100)
    type_contrat = models.CharField(max_length=20, choices=CONTRAT_CHOICES, default='CDI')
    datePublication = models.DateTimeField(auto_now_add=True)
    date_expiration = models.DateField(null=True, blank=True)
    recruteur = models.ForeignKey(Recruteur, on_delete=models.CASCADE, related_name='offres')

    def __str__(self):
        return self.titre


class StatutCandidature(models.Model):
    nom = models.CharField(max_length=50, unique=True)   
    type = models.CharField(max_length=50)
    acceptee = models.BooleanField(default=False)

    def __str__(self):
        return self.nom



class Candidature(models.Model):
    candidat = models.ForeignKey(Candidat, on_delete=models.CASCADE, related_name='candidatures')
    offre = models.ForeignKey(Offre, on_delete=models.CASCADE, related_name='candidatures')
    datePostulation = models.DateTimeField(auto_now_add=True)
    statut = models.ForeignKey(StatutCandidature, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return f"{self.candidat} → {self.offre.titre}"



class Document(models.Model):
    TYPE_CHOICES = [
    ('cv', 'CV'),
    ('lettre_motivation', 'Lettre de motivation'),
]
    candidat = models.ForeignKey(Candidat, on_delete=models.CASCADE, related_name='documents')
    type = models.CharField(max_length=50, choices=TYPE_CHOICES)   # CV, lettre_motivation
    fichier = models.FileField(upload_to='documents/')
    contenu = models.TextField(blank=True, null=True)
    date_upload = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.type} - {self.candidat}"


class Entretien(models.Model):
    TYPE_CHOICES = [
        ('physique', 'Physique'),
        ('visio', 'Visio'),
        ('telephone', 'Téléphone'),
    ]
    STATUT_CHOICES = [
        ('planifie', 'Planifié'),
        ('modifie', 'Modifié'),
        ('annule', 'Annulé'),
    ]

    date = models.DateField()
    heure = models.CharField(max_length=10)
    lieu = models.CharField(max_length=200)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='planifie')
    notes = models.TextField(blank=True)
    candidature = models.OneToOneField(Candidature, on_delete=models.CASCADE, related_name='entretien')

    def planifier(self):
        self.statut = 'planifie'
        self.save()

    def modifier(self):
        self.statut = 'modifie'
        self.save()

    def annuler(self):
        self.statut = 'annule'
        self.save()

    def notifierParticipants(self):
        pass

    def __str__(self):
        return f"Entretien le {self.date}"



class Message(models.Model):
    contenu = models.TextField()
    dateEnvoi = models.DateTimeField(auto_now_add=True)
    lu = models.BooleanField(default=False)
    expediteur = models.ForeignKey(Utilisateur, on_delete=models.CASCADE, related_name='messages_envoyes')
    destinataire = models.ForeignKey(Utilisateur, on_delete=models.CASCADE, related_name='messages_recus')

    def envoyer(self):
        self.save()

    def marquerCommeLu(self):
        self.lu = True
        self.save()

    def supprimer(self):
        self.delete()

    def __str__(self):
        return f"Message de {self.expediteur} → {self.destinataire}"




class Notification(models.Model):
    TYPE_CHOICES = [
        ('info', 'Information'),
        ('success', 'Succès'),
        ('warning', 'Alerte'),
        ('error', 'Erreur'),
    ]
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='info')
    contenu = models.TextField()
    dateEnvoi = models.DateTimeField(auto_now_add=True)
    lu = models.BooleanField(default=False)
    utilisateur = models.ForeignKey(Utilisateur, on_delete=models.CASCADE, related_name='notifications')

    def envoyer(self):
        self.save()

    def marquerCommeLu(self):
        self.lu = True
        self.save()

    def __str__(self):
        return f"Notification {self.type} pour {self.utilisateur}"

class Role(models.Model):
    nom = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    permissions = models.JSONField(default=list)

    def getPermissions(self):
        return self.permissions

    def ajouterPermission(self, permission):
        if permission not in self.permissions:
            self.permissions.append(permission)
            self.save()

    def supprimerPermission(self, permission):
        if permission in self.permissions:
            self.permissions.remove(permission)
            self.save()

    def __str__(self):
        return self.nom



class AppStatusHistory(models.Model):
    candidature = models.ForeignKey(Candidature, on_delete=models.CASCADE, related_name='historique')
    ancien_statut = models.ForeignKey(StatutCandidature, on_delete=models.SET_NULL, null=True, related_name='ancien_statuts')
    nouveau_statut = models.ForeignKey(StatutCandidature, on_delete=models.SET_NULL, null=True, related_name='nouveau_statuts')
    date_changement = models.DateTimeField(auto_now_add=True)
    modifie_par = models.ForeignKey(Utilisateur, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return f"{self.candidature} : {self.ancien_statut} → {self.nouveau_statut}"
'juste une amelioration makaynx f notre diag de classe'


class Dashboard:
    def __init__(self, recruteur=None):
        self.recruteur = recruteur

    @property
    def totalOffres(self):
        if self.recruteur:
            return self.recruteur.offres.count()
        return Offre.objects.count()

    @property
    def totalCandidatures(self):
        if self.recruteur:
            return Candidature.objects.filter(offre__recruteur=self.recruteur).count()
        return Candidature.objects.count()

    @property
    def totalUtilisateurs(self):
        return Utilisateur.objects.count()

    @property
    def tauxAcceptation(self):
        total = self.totalCandidatures
        if total == 0:
            return 0.0
        acceptees = Candidature.objects.filter(statut__acceptee=True).count()
        return (acceptees / total) * 100

    def genererStatistiques(self):
        return Statistiques(
            periode="globale",
            nombrePostulations=self.totalCandidatures,
            nombreEntretiens=Entretien.objects.count(),
            nombreEmbauches=Candidature.objects.filter(statut__acceptee=True).count()
        )

    def afficherActivite(self):
        pass


class Statistiques:
    def __init__(self, periode, nombrePostulations, nombreEntretiens, nombreEmbauches):
        self.periode = periode
        self.nombrePostulations = nombrePostulations
        self.nombreEntretiens = nombreEntretiens
        self.nombreEmbauches = nombreEmbauches

    def genererRapport(self):
        return (f"Période : {self.periode}\n"
                f"Postulations : {self.nombrePostulations}\n"
                f"Entretiens : {self.nombreEntretiens}\n"
                f"Embauches : {self.nombreEmbauches}")

    def exporter(self):
        pass