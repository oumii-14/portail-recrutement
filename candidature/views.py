from multiprocessing import context
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
from datetime import datetime, timedelta
from django.db.models.functions import TruncMonth
import csv
import os
from django.contrib.auth import authenticate, login
import django.contrib
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
from django.views.decorators.csrf import csrf_protect
from django.contrib.auth import authenticate, login
from .models import Utilisateur, Candidat, Recruteur, Offre, Candidature, Entretien, Notification, StatutCandidature, Document, Message, AppStatusHistory



# 1. FONCTIONS UTILITAIRES
def creer_notification(utilisateur, type_notif, contenu):
    Notification.objects.create(
        utilisateur=utilisateur,
        type=type_notif,
        contenu=contenu,
        dateEnvoi=timezone.now(),
        lu=False
    )


# =====================================================
# 2. AUTHENTIFICATION (inscription, connexion, déconnexion)
# =====================================================

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
            django.contrib.messages.error(request, 'Email ou mot de passe incorrect')
            return redirect('connexion')
    
    return render(request, 'candidature/connexion.html')

from django.views.decorators.csrf import csrf_protect
from django.contrib.auth import authenticate, login

@csrf_protect
def admin_login(request):
    if request.user.is_authenticated:
        if request.user.is_superuser or request.user.role == 'admin':
            return redirect('admin_dashboard')
        return redirect('dashboard')
    
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        user = authenticate(request, username=email, password=password)
        
        if user is not None:
            if user.is_superuser or user.role == 'admin':
                login(request, user)
                return redirect('admin_dashboard')
            else:
                django.contrib.messages.error(request, 'Vous n\'avez pas les droits administrateur')
                return redirect('admin_login')
        else:
            django.contrib.messages.error(request, 'Email ou mot de passe incorrect')
            return redirect('admin_login')
    
    return render(request, 'candidature/admin_login.html')

  





def deconnexion(request):
    logout(request)
    return redirect('accueil')


# =====================================================
# 3. PAGES PRINCIPALES (accueil, dashboard, profil, admin)
# =====================================================

def accueil(request):
    offres = Offre.objects.all().order_by('-datePublication')[:6]
    return render(request, 'candidature/accueil.html', {'offres': offres})


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
            context['offres_suggestions'] = Offre.objects.all().order_by('-datePublication')[:3]
            context['notifications_count'] = Notification.objects.filter(utilisateur=request.user, lu=False).count()
        except:
            context['candidatures_count'] = 0
            context['mes_candidatures'] = []
            context['offres'] = Offre.objects.all()
            context['entretiens_count'] = 0
            context['messages_non_lus'] = 0
            context['offres_suggestions'] = []
            context['notifications_count'] = 0
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
            context['notifications_count'] = Notification.objects.filter(utilisateur=request.user, lu=False).count()
            context['candidats_suggestions'] = Candidat.objects.all()[:3]
            context['offres_disponibles_count'] = Offre.objects.count()
        except:
            context['offres_count'] = 0
            context['mes_offres'] = []
            context['total_candidatures'] = 0
            context['dernieres_candidatures'] = []
            context['messages_non_lus'] = 0
            context['entretiens_a_venir'] = 0
            context['notifications_count'] = 0
            context['candidats_suggestions'] = []
            context['offres_disponibles_count'] = Offre.objects.count()

    # ========== ALEX - ASSISTANT INTELLIGENT ==========
    if request.user.role == 'candidat':
        try:
            candidat = Candidat.objects.get(utilisateur=request.user)
            
            if Candidature.objects.filter(candidat=candidat).count() == 0:
                alex_message = "📢 Tu n'as pas encore postulé. Consulte les offres et tente ta chance !"
            
            elif Candidature.objects.filter(candidat=candidat, statut__nom='acceptee').exists():
                alex_message = "🎉 Félicitations ! Une candidature a été acceptée. Contacte le recruteur."
            
            else:
                dernieres_candidatures = Candidature.objects.filter(candidat=candidat).order_by('-datePostulation')
                if dernieres_candidatures.exists():
                    derniere = dernieres_candidatures.first()
                    jours = (timezone.now().date() - derniere.datePostulation.date()).days
                    if jours > 7:
                        alex_message = f"📢 Ta dernière candidature date de {jours} jours. Postule à nouveau pour augmenter tes chances."
                    else:
                        alex_message = "💪 Continue comme ça ! Consulte les nouvelles offres régulièrement."
                else:
                    alex_message = "💪 Continue comme ça ! Consulte les nouvelles offres régulièrement."
        
        except:
            alex_message = "📢 Complète ton profil pour recevoir des conseils personnalisés."

    else:
        try:
            recruteur = Recruteur.objects.get(utilisateur=request.user)
            nouvelles = Candidature.objects.filter(offre__recruteur=recruteur, statut__nom='en_attente').count()
            
            if nouvelles > 0:
                alex_message = f"🔔 {nouvelles} nouvelle(s) candidature(s) en attente. Consulte-les maintenant."
            elif Offre.objects.filter(recruteur=recruteur).count() == 0:
                alex_message = "📢 Publie une offre pour attirer des candidats."
            else:
                alex_message = "📊 Tout est calme. Pense à promouvoir tes offres."
        
        except:
            alex_message = "📢 Complète ton profil pour recevoir des conseils."

    context['alex_message'] = alex_message
    
    return render(request, 'candidature/dashboard.html', context)


def mon_profil(request):
    return render(request, 'candidature/profil.html', {'user': request.user})


def admin_dashboard(request):
    from django.db.models import Count
    from datetime import date, datetime, timedelta

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
    
    # ========== DONNÉES POUR GRAPHIQUES ==========
    mois_labels = []
    inscriptions_data = []
    for i in range(5, -1, -1):
        mois = datetime.now() - timedelta(days=30*i)
        mois_labels.append(mois.strftime('%b %Y'))
        count = Utilisateur.objects.filter(
            dateCreation__year=mois.year, 
            dateCreation__month=mois.month
        ).count()
        inscriptions_data.append(count)
    
    top_offres = Offre.objects.annotate(total_candidatures=Count('candidatures')).order_by('-total_candidatures')[:5]
    offres_populaires_labels = [offre.titre[:20] for offre in top_offres]
    offres_populaires_data = [offre.total_candidatures for offre in top_offres]
    
    context.update({
        'mois_labels': mois_labels,
        'inscriptions_data': inscriptions_data,
        'offres_populaires_labels': offres_populaires_labels,
        'offres_populaires_data': offres_populaires_data,
    })
    
    return render(request, 'candidature/admin_dashboard.html', context)


# =====================================================
# 4. GESTION DES OFFRES (CRUD)
# =====================================================

@login_required
def creer_offre(request):
    if not request.user.is_authenticated or request.user.role != 'recruteur':
        return redirect('accueil')
    
    if request.method == 'POST':
        titre = request.POST.get('titre')
        description = request.POST.get('description')
        lieu = request.POST.get('lieu')
        type_contrat = request.POST.get('type_contrat')
        date_expiration = request.POST.get('date_expiration')
        
        if not date_expiration:
            date_expiration = None
        
        recruteur = Recruteur.objects.get(utilisateur=request.user)
        
        Offre.objects.create(
            titre=titre,
            description=description,
            lieu=lieu,
            type_contrat=type_contrat,
            date_expiration=date_expiration,
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
        offre.type_contrat = request.POST.get('type_contrat')
        date_expiration = request.POST.get('date_expiration')
        offre.date_expiration = date_expiration if date_expiration else None
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


# =====================================================
# 5. GESTION DES CANDIDATURES (postuler, accepter, refuser, entretien)
# =====================================================

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
        lettre_motivation = request.POST.get('lettre_motivation')
        
        if not cv:
            return render(request, 'candidature/postuler.html', {
                'offre': offre,
                'erreur': 'Veuillez joindre votre CV.'
            })
        
        if not lettre_motivation:
            return render(request, 'candidature/postuler.html', {
                'offre': offre,
                'erreur': 'Veuillez rédiger votre lettre de motivation.'
            })
        
        statut_attente = StatutCandidature.objects.get(nom='en_attente')
        candidature = Candidature.objects.create(
            candidat=candidat,
            offre=offre,
            statut=statut_attente
        )
        
        # Sauvegarde du CV
        Document.objects.create(
            candidat=candidat,
            type='cv',
            fichier=cv,
            date_upload=timezone.now()
        )
        
        # Sauvegarde de la lettre de motivation (avec contenu texte)
        Document.objects.create(
            candidat=candidat,
            type='lettre_motivation',
            fichier=None,
            contenu=lettre_motivation,
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
    
    # Calcul des statistiques
    total_candidatures = candidatures.count()
    en_attente_count = candidatures.filter(statut__nom='en_attente').count()
    acceptee_count = candidatures.filter(statut__nom='acceptee').count()
    entretien_count = candidatures.filter(statut__nom='entretien').count()
    
    return render(request, 'candidature/mes_candidatures.html', {
        'candidatures': candidatures,
        'total_candidatures': total_candidatures,
        'en_attente_count': en_attente_count,
        'acceptee_count': acceptee_count,
        'entretien_count': entretien_count,
    })


@login_required
def candidatures_recues(request):
    if request.user.role != 'recruteur':
        return redirect('dashboard')
    
    recruteur = Recruteur.objects.get(utilisateur=request.user)
    offres = Offre.objects.filter(recruteur=recruteur)
    candidatures = Candidature.objects.filter(offre__in=offres).order_by('-datePostulation')
    
    # Filtre par statut
    statut_filter = request.GET.get('statut')
    if statut_filter:
        candidatures = candidatures.filter(statut__nom=statut_filter)
    
    # Filtre par ville
    ville_filter = request.GET.get('ville')
    if ville_filter:
        candidatures = candidatures.filter(offre__lieu__icontains=ville_filter)
    
    # 🔥 FILTRE PAR CANDIDAT (via user_id)
    user_id = request.GET.get('user')
    if user_id:
        candidatures = candidatures.filter(candidat__utilisateur__id=user_id)
    
    statuts = StatutCandidature.objects.all()
    villes = Offre.objects.filter(recruteur=recruteur).values_list('lieu', flat=True).distinct()
    
    return render(request, 'candidature/candidatures_recues.html', {
        'candidatures': candidatures,
        'statuts': statuts,
        'villes': villes,
        'statut_filter': statut_filter,
        'ville_filter': ville_filter,
        'user_id': user_id,
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
def entretiens(request):
    """
    Affiche les entretiens :
    - Pour le candidat : entretiens liés à ses candidatures
    - Pour le recruteur : entretiens liés à ses offres
    """
    user = request.user
    
    if user.role == 'candidat':
        try:
            candidat = Candidat.objects.get(utilisateur=user)
            entretiens_list = Entretien.objects.filter(
                candidature__candidat=candidat
            ).order_by('date', 'heure')
        except Candidat.DoesNotExist:
            entretiens_list = []
    
    elif user.role == 'recruteur':
        try:
            recruteur = Recruteur.objects.get(utilisateur=user)
            entretiens_list = Entretien.objects.filter(
                candidature__offre__recruteur=recruteur
            ).order_by('date', 'heure')
        except Recruteur.DoesNotExist:
            entretiens_list = []
    
    else:
        entretiens_list = []
    
    context = {
        'entretiens': entretiens_list,
        'user': user,
    }
    
    return render(request, 'candidature/entretiens.html', context)


@login_required
def modifier_entretien(request, entretien_id):
    entretien = Entretien.objects.get(id=entretien_id)
    
    # Vérifier que l'utilisateur est le recruteur concerné
    if request.user.role != 'recruteur' or entretien.candidature.offre.recruteur.utilisateur != request.user:
        return redirect('dashboard')
    
    if request.method == 'POST':
        entretien.date = request.POST['date']
        entretien.heure = request.POST['heure']
        entretien.lieu = request.POST['lieu']
        entretien.type = request.POST['type']
        entretien.save()
        
        # Notifier le candidat du changement
        creer_notification(
            utilisateur=entretien.candidature.candidat.utilisateur,
            type_notif='info',
            contenu=f"L'entretien pour l'offre {entretien.candidature.offre.titre} a été modifié. Nouvelle date: {entretien.date} à {entretien.heure}"
        )
        
        return redirect('entretiens')
    
    return render(request, 'candidature/modifier_entretien.html', {'entretien': entretien})


# =====================================================
# 6. COMMUNICATION (messages, notifications)
# =====================================================

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
            django.contrib.messages.success(request, 'Message envoyé !')
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


# =====================================================
# 7. ASSISTANT INTELLIGENT ALEX
# =====================================================

def alex_offre_ideale(request):
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
        
        return render(request, 'candidature/alex_resultat.html', {
            'offre': meilleure_offre,
            'score': meilleur_score,
            'poste': poste,
            'ville': ville,
            'contrat': contrat
        })
    
    return render(request, 'candidature/alex_offre_ideale.html')


def alex_aide_offre(request):
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
        
        return render(request, 'candidature/alex_aide_offre_resultat.html', {
            'titre': titre,
            'description': description,
            'lieu': lieu
        })
    
    return render(request, 'candidature/alex_aide_offre.html')


# =====================================================
# 8. ARTICLES BLOG
# =====================================================

def blog_cv_conseils(request):
    return render(request, 'candidature/blog_cv_conseils.html')


def blog_preparer_entretien(request):
    return render(request, 'candidature/blog_preparer_entretien.html')


def blog_tendances_2026(request):
    return render(request, 'candidature/blog_tendances_2026.html')

@login_required
def export_statistiques(request):
    """Exporte toutes les statistiques en CSV pour l'admin"""
    if request.user.role != 'admin':
        return redirect('dashboard')
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="statistiques_obmi.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['📊 STATISTIQUES OBMIRECRUTEMENT', ''])
    writer.writerow(['Date export', datetime.now().strftime('%d/%m/%Y %H:%M')])
    writer.writerow([])
    writer.writerow(['Indicateur', 'Valeur'])
    writer.writerow(['Offres publiées', Offre.objects.count()])
    writer.writerow(['Candidats inscrits', Candidat.objects.count()])
    writer.writerow(['Recruteurs inscrits', Recruteur.objects.count()])
    writer.writerow(['Candidatures reçues', Candidature.objects.count()])
    writer.writerow(['Entretiens planifiés', Entretien.objects.count()])
    writer.writerow(['Messages échangés', Message.objects.count()])
    writer.writerow([])
    writer.writerow(['📋 RÉPARTITION DES CANDIDATURES', ''])
    writer.writerow(['En attente', Candidature.objects.filter(statut__nom='en_attente').count()])
    writer.writerow(['Acceptées', Candidature.objects.filter(statut__nom='acceptee').count()])
    writer.writerow(['Refusées', Candidature.objects.filter(statut__nom='rejetee').count()])
    writer.writerow(['Entretien', Candidature.objects.filter(statut__nom='entretien').count()])
    
    return response

@login_required
def generer_rapport_pdf(request):
    """Génère un rapport PDF complet pour l'admin"""
    if request.user.role != 'admin':
        return redirect('dashboard')
    
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.pdfgen import canvas
    from reportlab.lib.colors import HexColor
    import io
    
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=landscape(A4))
    width, height = landscape(A4)
    
    # En-tête
    p.setFont("Helvetica-Bold", 20)
    p.setFillColor(HexColor('#1E3A5F'))
    p.drawString(50, height - 50, "OBMI Recrutement - Rapport d'activité")
    
    p.setFont("Helvetica", 10)
    p.setFillColor(HexColor('#666666'))
    p.drawString(50, height - 75, f"Généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}")
    p.line(50, height - 90, width - 50, height - 90)
    
    # Section 1 : Statistiques générales
    y = height - 130
    p.setFont("Helvetica-Bold", 14)
    p.drawString(50, y, "1. Statistiques générales")
    y -= 30
    
    p.setFont("Helvetica", 11)
    stats = [
        f"📄 Offres publiées : {Offre.objects.count()}",
        f"👥 Candidats inscrits : {Candidat.objects.count()}",
        f"🏢 Recruteurs inscrits : {Recruteur.objects.count()}",
        f"📋 Candidatures reçues : {Candidature.objects.count()}",
        f"🎤 Entretiens planifiés : {Entretien.objects.count()}",
        f"💬 Messages échangés : {Message.objects.count()}",
    ]
    for stat in stats:
        p.drawString(70, y, stat)
        y -= 22
    
    # Section 2 : Répartition des candidatures
    y -= 20
    p.setFont("Helvetica-Bold", 14)
    p.drawString(50, y, "2. Répartition des candidatures")
    y -= 30
    
    p.setFont("Helvetica", 11)
    p.drawString(70, y, f"⏳ En attente : {Candidature.objects.filter(statut__nom='en_attente').count()}")
    y -= 22
    p.drawString(70, y, f"✅ Acceptées : {Candidature.objects.filter(statut__nom='acceptee').count()}")
    y -= 22
    p.drawString(70, y, f"❌ Refusées : {Candidature.objects.filter(statut__nom='rejetee').count()}")
    y -= 22
    p.drawString(70, y, f"📅 Entretien : {Candidature.objects.filter(statut__nom='entretien').count()}")
    
    # Section 3 : Top offres
    y -= 40
    p.setFont("Helvetica-Bold", 14)
    p.drawString(50, y, "3. Offres les plus populaires")
    y -= 30
    
    top_offres = Offre.objects.annotate(total=Count('candidatures')).order_by('-total')[:5]
    p.setFont("Helvetica", 11)
    for offre in top_offres:
        p.drawString(70, y, f"• {offre.titre} : {offre.total} candidature(s)")
        y -= 22
    
    # Pied de page
    p.setFont("Helvetica", 8)
    p.setFillColor(HexColor('#999999'))
    p.drawString(width - 150, 30, "OBMI Recrutement - Rapport automatique")
    
    p.save()
    buffer.seek(0)
    
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="rapport_obmi.pdf"'
    return response

@login_required
def mes_documents(request):
    """Liste des documents du candidat"""
    if request.user.role != 'candidat':
        return redirect('dashboard')
    
    candidat = Candidat.objects.get(utilisateur=request.user)
    documents = Document.objects.filter(candidat=candidat).order_by('-date_upload')
    
    return render(request, 'candidature/mes_documents.html', {'documents': documents})


@login_required
def supprimer_document(request, doc_id):
    """Supprime un document (CV, lettre de motivation)"""
    doc = Document.objects.get(id=doc_id)
    
    # Vérifier que le document appartient au candidat connecté
    if doc.candidat.utilisateur != request.user:
        return redirect('dashboard')
    
    # Supprimer le fichier physique
    if doc.fichier and os.path.isfile(doc.fichier.path):
        os.remove(doc.fichier.path)
    
    doc.delete()
    django.contrib.messages.success(request, "Document supprimé avec succès")
    return redirect('mes_documents')

@login_required
def export_statistiques(request):
    """Exporte toutes les statistiques en CSV (compatible Excel)"""
   
    
    # Encodage UTF-8 avec BOM pour Excel
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="statistiques_obmi.csv"'
    response.write('\ufeff'.encode('utf8'))  # BOM pour Excel
    
    writer = csv.writer(response, delimiter=';')  # Point-virgule pour Excel français
    
    writer.writerow(['STATISTIQUES OBMIRECRUTEMENT', ''])
    writer.writerow(['Date export', datetime.now().strftime('%d/%m/%Y %H:%M')])
    writer.writerow([])
    writer.writerow(['Indicateur', 'Valeur'])
    writer.writerow(['Offres publiees', Offre.objects.count()])
    writer.writerow(['Candidats inscrits', Candidat.objects.count()])
    writer.writerow(['Recruteurs inscrits', Recruteur.objects.count()])
    writer.writerow(['Candidatures recues', Candidature.objects.count()])
    writer.writerow(['Entretiens planifies', Entretien.objects.count()])
    writer.writerow(['Messages echanges', Message.objects.count()])
    writer.writerow([])
    writer.writerow(['REPARTITION DES CANDIDATURES', ''])
    writer.writerow(['En attente', Candidature.objects.filter(statut__nom='en_attente').count()])
    writer.writerow(['Acceptees', Candidature.objects.filter(statut__nom='acceptee').count()])
    writer.writerow(['Refusees', Candidature.objects.filter(statut__nom='rejetee').count()])
    writer.writerow(['Entretien', Candidature.objects.filter(statut__nom='entretien').count()])
    
    return response


@login_required
def generer_rapport_pdf(request):
    """Génère un rapport PDF complet"""
    # Supprime ou commente cette ligne temporairement
    # if not (request.user.is_superuser or request.user.role == 'admin'):
    #     return redirect('dashboard')
    
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.pdfgen import canvas
    from reportlab.lib.colors import HexColor
    from django.db.models import Count
    import io
    
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=landscape(A4))
    width, height = landscape(A4)
    
    # En-tête
    p.setFont("Helvetica-Bold", 20)
    p.setFillColor(HexColor('#1E3A5F'))
    p.drawString(50, height - 50, "OBMI Recrutement - Rapport d'activité")
    
    p.setFont("Helvetica", 10)
    p.setFillColor(HexColor('#666666'))
    p.drawString(50, height - 75, f"Généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}")
    p.line(50, height - 90, width - 50, height - 90)
    
    # Section 1 : Statistiques générales
    y = height - 130
    p.setFont("Helvetica-Bold", 14)
    p.drawString(50, y, "1. Statistiques générales")
    y -= 30
    
    p.setFont("Helvetica", 11)
    stats = [
        f"📄 Offres publiées : {Offre.objects.count()}",
        f"👥 Candidats inscrits : {Candidat.objects.count()}",
        f"🏢 Recruteurs inscrits : {Recruteur.objects.count()}",
        f"📋 Candidatures reçues : {Candidature.objects.count()}",
        f"🎤 Entretiens planifiés : {Entretien.objects.count()}",
        f"💬 Messages échangés : {Message.objects.count()}",
    ]
    for stat in stats:
        p.drawString(70, y, stat)
        y -= 22
    
    # Section 2 : Répartition des candidatures
    y -= 20
    p.setFont("Helvetica-Bold", 14)
    p.drawString(50, y, "2. Répartition des candidatures")
    y -= 30
    
    p.setFont("Helvetica", 11)
    p.drawString(70, y, f"⏳ En attente : {Candidature.objects.filter(statut__nom='en_attente').count()}")
    y -= 22
    p.drawString(70, y, f"✅ Acceptées : {Candidature.objects.filter(statut__nom='acceptee').count()}")
    y -= 22
    p.drawString(70, y, f"❌ Refusées : {Candidature.objects.filter(statut__nom='rejetee').count()}")
    y -= 22
    p.drawString(70, y, f"📅 Entretien : {Candidature.objects.filter(statut__nom='entretien').count()}")
    
    # Section 3 : Top offres
    y -= 40
    p.setFont("Helvetica-Bold", 14)
    p.drawString(50, y, "3. Offres les plus populaires")
    y -= 30
    
    top_offres = Offre.objects.annotate(total=Count('candidatures')).order_by('-total')[:5]
    p.setFont("Helvetica", 11)
    for offre in top_offres:
        p.drawString(70, y, f"• {offre.titre} : {offre.total} candidature(s)")
        y -= 22
    
    # Pied de page
    p.setFont("Helvetica", 8)
    p.setFillColor(HexColor('#999999'))
    p.drawString(width - 150, 30, "OBMI Recrutement - Rapport automatique")
    
    p.save()
    buffer.seek(0)
    
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="rapport_obmi.pdf"'
    return response