from django.contrib import admin
from .models import AppStatusHistory, Document, Utilisateur, Candidat, Recruteur, Offre, Candidature, StatutCandidature, Entretien, Message, Notification, Role,Document

admin.site.register(Utilisateur)
admin.site.register(Candidat)
admin.site.register(Recruteur)
admin.site.register(Offre)
admin.site.register(Candidature)
admin.site.register(StatutCandidature)
admin.site.register(Entretien)
admin.site.register(Message)
admin.site.register(Notification)
admin.site.register(Role)
admin.site.register(AppStatusHistory)
admin.site.register(Document)
