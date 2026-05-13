import zipfile
from django.db import models
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import FileResponse, HttpResponse
from django.utils import timezone
from datetime import date
from django.db.models import Count
import csv
import os
from .models import Utilisateur, Candidat, Recruteur, Offre, Candidature, Entretien, Notification, StatutCandidature, Document, Message, AppStatusHistory

def creer_notification(utilisateur, type_notif, contenu):
    Notification.objects.create(
        utilisateur=utilisateur,
        type=type_notif,
        contenu=contenu,
        dateEnvoi=timezone.now(),
        lu=False
    )

def accueil(request):
    return render(request, 'candidature/accueil.html')

def inscription(request):
    if request.method == 'POST':
        nom = request.POST.get('nom')
        prenom = request.POST.get('prenom')
        email = request.POST.get('email')
        password = request.POST.get('password')
        role = request.POST.get('role', 'candidat')
        
        if Utilisateur.objects.filter(email=email).exists():
            return HttpResponse("""
            <!DOCTYPE html>
            <html><head><title>Erreur</title>
            <style>body{background:linear-gradient(135deg,#667eea,#764ba2);min-height:100vh;display:flex;justify-content:center;align-items:center;font-family:Arial}
            .card{background:white;border-radius:20px;padding:40px;text-align:center}
            a{color:#667eea;text-decoration:none}
            </style>
            </head>
            <body>
            <div class='card'><h2> Erreur</h2><p>Cet email existe déjà.</p><a href='/inscription/'>Réessayer</a></div>
            </body>
            </html>
            """)
        
        user = Utilisateur.objects.create_user(
            username=email,
            email=email,
            password=password,
            nom=nom,
            prenom=prenom,
            role=role
        )
        
        if role == 'candidat':
            Candidat.objects.create(utilisateur=user)
        else:
            Recruteur.objects.create(utilisateur=user, entreprise="", telephone="", departement="")
        
        login(request, user)
        return redirect('/dashboard/')
    
    return render(request, 'candidature/inscription.html')

def connexion(request):  
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        user = authenticate(request, username=email, password=password)
        
        if user:
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, 'Email ou mot de passe incorrect')
            return redirect('connexion')
    
    return render(request, 'candidature/connexion.html')

def dashboard(request):
    if not request.user.is_authenticated:
        return redirect('connexion')
    
    context = {'user': request.user}
    
    if request.user.role == 'candidat':
        try:
            candidat = Candidat.objects.get(utilisateur=request.user)
            context['candidatures_count'] = candidat.candidatures.count()
            context['mes_candidatures'] = candidat.candidatures.all()
            context['offres'] = Offre.objects.all()
            context['entretiens_count'] = Entretien.objects.filter(candidature__candidat=candidat).count()
            context['messages_non_lus'] = Message.objects.filter(destinataire=request.user, lu=False).count()
        except:
            context['candidatures_count'] = 0
            context['mes_candidatures'] = []
            context['offres'] = Offre.objects.all()
            context['entretiens_count'] = 0
            context['messages_non_lus'] = 0
    else:
        try:
            recruteur = Recruteur.objects.get(utilisateur=request.user)
            context['offres_count'] = recruteur.offres.count()
            context['mes_offres'] = recruteur.offres.all()
            context['total_candidatures'] = 0
            for offre in recruteur.offres.all():
                context['total_candidatures'] += offre.candidatures.count()
            context['dernieres_candidatures'] = Candidature.objects.filter(offre__recruteur=recruteur).order_by('-datePostulation')[:5]
            context['messages_non_lus'] = Message.objects.filter(destinataire=request.user, lu=False).count()
            context['entretiens_a_venir'] = Entretien.objects.filter(date__gte=date.today()).count()
        except:
            context['offres_count'] = 0
            context['mes_offres'] = []
            context['total_candidatures'] = 0
            context['dernieres_candidatures'] = []
            context['messages_non_lus'] = 0
            context['entretiens_a_venir'] = 0

    # ========== OULAY - ASSISTANT INTELLIGENT ==========
    if request.user.role == 'candidat':
        try:
            candidat = Candidat.objects.get(utilisateur=request.user)
            
            if Candidature.objects.filter(candidat=candidat).count() == 0:
                oulay_message = "📢 Tu n'as pas encore postulé. Consulte les offres et tente ta chance !"
            
            elif Candidature.objects.filter(candidat=candidat, statut__nom='acceptee').exists():
                oulay_message = "🎉 Félicitations ! Une candidature a été acceptée. Contacte le recruteur."
            
            else:
                dernieres_candidatures = Candidature.objects.filter(candidat=candidat).order_by('-datePostulation')
                if dernieres_candidatures.exists():
                    derniere = dernieres_candidatures.first()
                    jours = (timezone.now().date() - derniere.datePostulation.date()).days
                    if jours > 7:
                        oulay_message = f"📢 Ta dernière candidature date de {jours} jours. Postule à nouveau pour augmenter tes chances."
                    else:
                        oulay_message = "💪 Continue comme ça ! Consulte les nouvelles offres régulièrement."
                else:
                    oulay_message = "💪 Continue comme ça ! Consulte les nouvelles offres régulièrement."
        
        except:
            oulay_message = "📢 Complète ton profil pour recevoir des conseils personnalisés."

    else:
        try:
            recruteur = Recruteur.objects.get(utilisateur=request.user)
            nouvelles = Candidature.objects.filter(offre__recruteur=recruteur, statut__nom='en_attente').count()
            
            if nouvelles > 0:
                oulay_message = f"🔔 {nouvelles} nouvelle(s) candidature(s) en attente. Consulte-les maintenant."
            elif Offre.objects.filter(recruteur=recruteur).count() == 0:
                oulay_message = "📢 Publie une offre pour attirer des candidats."
            else:
                oulay_message = "📊 Tout est calme. Pense à promouvoir tes offres."
        
        except:
            oulay_message = "📢 Complète ton profil pour recevoir des conseils."

    context['oulay_message'] = oulay_message
    
    return render(request, 'candidature/dashboard.html', context)

def deconnexion(request):
    logout(request)
    return redirect('accueil')

@login_required
def creer_offre(request):
    if not request.user.is_authenticated or request.user.role != 'recruteur':
        return redirect('accueil')
    
    if request.method == 'POST':
        titre = request.POST.get('titre')
        description = request.POST.get('description')
        lieu = request.POST.get('lieu')
        
        recruteur = Recruteur.objects.get(utilisateur=request.user)
        
        Offre.objects.create(
            titre=titre,
            description=description,
            lieu=lieu,
            recruteur=recruteur
        )
        
        return redirect('dashboard')
    
    return render(request, 'candidature/creer_offre.html')

@login_required
def mes_offres(request):
    if request.user.role != 'recruteur':
        return redirect('dashboard')
    recruteur = Recruteur.objects.get(utilisateur=request.user)
    offres = Offre.objects.filter(recruteur=recruteur)
    return render(request, 'candidature/mes_offres.html', {'offres': offres})

@login_required
def modifier_offre(request, offre_id):
    offre = Offre.objects.get(id=offre_id)
    
    if request.user.role != 'recruteur' or offre.recruteur.utilisateur != request.user:
        return redirect('dashboard')
    
    if request.method == 'POST':
        offre.titre = request.POST['titre']
        offre.description = request.POST['description']
        offre.lieu = request.POST['lieu']
        offre.save()
        return redirect('dashboard')
    
    return render(request, 'candidature/modifier_offre.html', {'offre': offre})

@login_required
def supprimer_offre(request, offre_id):
    offre = Offre.objects.get(id=offre_id)
    
    if request.user.role != 'recruteur' or offre.recruteur.utilisateur != request.user:
        return redirect('dashboard')
    
    offre.delete()
    return redirect('dashboard')

@login_required
def liste_offres(request):
    offres = Offre.objects.all().order_by('-datePublication')
    query = request.GET.get('q')
    if query:
        offres = offres.filter(titre__icontains=query) | offres.filter(lieu__icontains=query)
    return render(request, 'candidature/liste_offres.html', {'offres': offres, 'query': query})

@login_required
def postuler(request, offre_id):
    if request.user.role != 'candidat':
        return redirect('dashboard')
    
    offre = Offre.objects.get(id=offre_id)
    candidat = Candidat.objects.get(utilisateur=request.user)
    
    deja_postule = Candidature.objects.filter(candidat=candidat, offre=offre).exists()
    
    if request.method == 'POST':
        if deja_postule:
            return render(request, 'candidature/postuler.html', {
                'offre': offre,
                'erreur': 'Vous avez déjà postulé à cette offre.'
            })
        
        cv = request.FILES.get('cv')
        
        if not cv:
            return render(request, 'candidature/postuler.html', {
                'offre': offre,
                'erreur': 'Veuillez joindre votre CV.'
            })
        
        statut_attente = StatutCandidature.objects.get(nom='en_attente')
        candidature = Candidature.objects.create(
            candidat=candidat,
            offre=offre,
            statut=statut_attente
        )
        
        Document.objects.create(
            candidat=candidat,
            type='cv',
            fichier=cv,
            date_upload=timezone.now()
        )
        
        creer_notification(
            utilisateur=offre.recruteur.utilisateur,
            type_notif='info',
            contenu=f"Nouvelle candidature de {candidat.utilisateur.prenom} {candidat.utilisateur.nom} pour l'offre {offre.titre}"
        )
        
        return redirect('dashboard')
    
    return render(request, 'candidature/postuler.html', {'offre': offre})

@login_required
def mes_candidatures(request):
    if request.user.role != 'candidat':
        return redirect('dashboard')
    
    candidat = Candidat.objects.get(utilisateur=request.user)
    candidatures = Candidature.objects.filter(candidat=candidat).order_by('-datePostulation')
    
    return render(request, 'candidature/mes_candidatures.html', {'candidatures': candidatures})

@login_required
def candidatures_recues(request):
    if request.user.role != 'recruteur':
        return redirect('dashboard')
    
    recruteur = Recruteur.objects.get(utilisateur=request.user)
    offres = Offre.objects.filter(recruteur=recruteur)
    candidatures = Candidature.objects.filter(offre__in=offres).order_by('-datePostulation')
    
    statut_filter = request.GET.get('statut')
    ville_filter = request.GET.get('ville')
    
    if statut_filter:
        candidatures = candidatures.filter(statut__nom=statut_filter)
    if ville_filter:
        candidatures = candidatures.filter(offre__lieu__icontains=ville_filter)
    
    statuts = StatutCandidature.objects.all()
    villes = Offre.objects.filter(recruteur=recruteur).values_list('lieu', flat=True).distinct()
    
    return render(request, 'candidature/candidatures_recues.html', {
        'candidatures': candidatures,
        'statuts': statuts,
        'villes': villes,
        'statut_filter': statut_filter,
        'ville_filter': ville_filter,
    })

@login_required
def accepter_candidature(request, candidature_id):
    candidature = Candidature.objects.get(id=candidature_id)
    statut_accepte = StatutCandidature.objects.get(nom='acceptee')
    candidature.statut = statut_accepte
    candidature.save()
    
    creer_notification(
        utilisateur=candidature.candidat.utilisateur,
        type_notif='success',
        contenu=f"Votre candidature pour l'offre {candidature.offre.titre} a été acceptée !"
    )
    
    return redirect('candidatures_recues')

@login_required
def rejeter_candidature(request, candidature_id):
    candidature = Candidature.objects.get(id=candidature_id)
    statut_rejete = StatutCandidature.objects.get(nom='rejetee')
    candidature.statut = statut_rejete
    candidature.save()
    
    creer_notification(
        utilisateur=candidature.candidat.utilisateur,
        type_notif='error',
        contenu=f"Votre candidature pour l'offre {candidature.offre.titre} a été refusée."
    )
    
    return redirect('candidatures_recues')

@login_required
def planifier_entretien(request, candidature_id):
    candidature = Candidature.objects.get(id=candidature_id)
    
    if request.user.role != 'recruteur':
        return redirect('dashboard')
    
    if request.method == 'POST':
        date_entretien = request.POST['date']
        heure = request.POST['heure']
        lieu = request.POST['lieu']
        type_entretien = request.POST['type']
        
        Entretien.objects.create(
            candidature=candidature,
            date=date_entretien,
            heure=heure,
            lieu=lieu,
            type=type_entretien,
            statut='planifie',
            notes=''
        )
        
        try:
            statut_entretien = StatutCandidature.objects.get(nom='entretien')
        except:
            statut_entretien = StatutCandidature.objects.create(
                nom='entretien',
                type='intermediaire',
                acceptee=False
            )
        candidature.statut = statut_entretien
        candidature.save()
        
        creer_notification(
            utilisateur=candidature.candidat.utilisateur,
            type_notif='info',
            contenu=f"Un entretien a été planifié pour votre candidature à l'offre {candidature.offre.titre}. Date: {date_entretien} à {heure} - Lieu: {lieu}"
        )
        
        return redirect('candidatures_recues')
    
    return render(request, 'candidature/planifier_entretien.html', {'candidature': candidature})

@login_required
def messages_liste(request):
    conversations = {}
    messages_recus = Message.objects.filter(destinataire=request.user).order_by('-dateEnvoi')
    messages_envoyes = Message.objects.filter(expediteur=request.user).order_by('-dateEnvoi')
    
    for msg in messages_recus:
        conversations[msg.expediteur.id] = msg.expediteur
    for msg in messages_envoyes:
        conversations[msg.destinataire.id] = msg.destinataire
    
    return render(request, 'candidature/messages_liste.html', {
        'conversations': conversations.values(),
        'messages_recus': messages_recus[:5]
    })

@login_required
def envoyer_message(request):
    if request.method == 'POST':
        destinataire_id = request.POST.get('destinataire')
        contenu = request.POST.get('contenu')
        
        if destinataire_id and contenu:
            destinataire = Utilisateur.objects.get(id=destinataire_id)
            Message.objects.create(
                expediteur=request.user,
                destinataire=destinataire,
                contenu=contenu
            )
            creer_notification(
                utilisateur=destinataire,
                type_notif='info',
                contenu=f"Nouveau message de {request.user.prenom} {request.user.nom}"
            )
            messages.success(request, 'Message envoyé !')
            return redirect('messages_liste')
    
    utilisateurs = Utilisateur.objects.exclude(id=request.user.id)
    return render(request, 'candidature/envoyer_message.html', {'utilisateurs': utilisateurs})

@login_required
def conversation(request, utilisateur_id):
    autre = Utilisateur.objects.get(id=utilisateur_id)
    messages_list = Message.objects.filter(
        expediteur=request.user, destinataire=autre
    ) | Message.objects.filter(
        expediteur=autre, destinataire=request.user
    ).order_by('dateEnvoi')
    
    Message.objects.filter(expediteur=autre, destinataire=request.user, lu=False).update(lu=True)
    
    return render(request, 'candidature/conversation.html', {
        'autre': autre,
        'messages': messages_list
    })

@login_required
def mes_notifications(request):
    notifications = Notification.objects.filter(utilisateur=request.user).order_by('-dateEnvoi')
    return render(request, 'candidature/notifications.html', {'notifications': notifications})

@login_required
def entretiens_liste(request):
    if request.user.role != 'recruteur':
        return redirect('dashboard')
    
    recruteur = Recruteur.objects.get(utilisateur=request.user)
    entretiens = Entretien.objects.filter(candidature__offre__recruteur=recruteur).order_by('date')
    
    return render(request, 'candidature/entretiens.html', {'entretiens': entretiens})

@login_required
def mon_profil(request):
    return render(request, 'candidature/profil.html', {'user': request.user})

def admin_dashboard(request):
    from django.db.models import Count
    from datetime import date

    context = {
        'total_offres': Offre.objects.count(),
        'total_candidats': Candidat.objects.count(),
        'total_recruteurs': Recruteur.objects.count(),
        'total_candidatures': Candidature.objects.count(),
        'total_entretiens': Entretien.objects.count(),
        'total_messages': Message.objects.count(),
        
        'candidatures_attente': Candidature.objects.filter(statut__nom='en_attente').count(),
        'candidatures_acceptees': Candidature.objects.filter(statut__nom='acceptee').count(),
        'candidatures_refusees': Candidature.objects.filter(statut__nom='rejetee').count(),
        'candidatures_entretien': Candidature.objects.filter(statut__nom='entretien').count(),
        
        'offres_populaires': Offre.objects.annotate(total_candidatures=Count('candidatures')).order_by('-total_candidatures')[:5],
        'entretiens_a_venir': Entretien.objects.filter(date__gte=date.today()).order_by('date')[:10],
        'dernieres_candidatures': Candidature.objects.all().order_by('-datePostulation')[:10],
        'derniers_utilisateurs': Utilisateur.objects.all().order_by('-dateCreation')[:10],
    }
    
    return render(request, 'candidature/admin_dashboard.html', context)

def oulay_offre_ideale(request):
    if request.method == 'POST':
        poste = request.POST.get('poste', '').lower()
        ville = request.POST.get('ville', '').lower()
        contrat = request.POST.get('contrat', '').lower()
        
        offres = Offre.objects.all()
        meilleure_offre = None
        meilleur_score = 0
        
        for offre in offres:
            score = 0
            if poste in offre.titre.lower():
                score += 2
            if ville in offre.lieu.lower():
                score += 2
            if contrat in offre.description.lower():
                score += 1
            
            if score > meilleur_score:
                meilleur_score = score
                meilleure_offre = offre
        
        return render(request, 'candidature/oulay_resultat.html', {
            'offre': meilleure_offre,
            'score': meilleur_score,
            'poste': poste,
            'ville': ville,
            'contrat': contrat
        })
    
    return render(request, 'candidature/oulay_offre_ideale.html')

def oulay_aide_offre(request):
    if request.method == 'POST':
        titre = request.POST.get('titre')
        secteur = request.POST.get('secteur')
        lieu = request.POST.get('lieu')
        
        description = f"""📢 POSTE : {titre}

👥 Secteur : {secteur}
📍 Localisation : {lieu}

📌 Missions :
- Participer activement aux projets liés au {secteur}
- Contribuer à l’atteinte des objectifs de l’équipe
- Proposer des améliorations continues

🎯 Profil recherché :
- Expérience significative dans le domaine
- Rigueur, autonomie et esprit d’équipe
- Capacité d’adaptation et force de proposition

✨ Ce que nous offrons :
- Environnement de travail dynamique
- Opportunités d’évolution
- Package salarial attractif

Postulez dès maintenant et rejoignez une équipe passionnée !"""
        
        return render(request, 'candidature/oulay_aide_offre_resultat.html', {
            'titre': titre,
            'description': description,
            'lieu': lieu
        })
    
    return render(request, 'candidature/oulay_aide_offre.html')