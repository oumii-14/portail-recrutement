from django.test import TestCase, Client
from django.urls import reverse
from .models import Utilisateur, Candidat, Recruteur, Offre, Candidature, StatutCandidature


class InscriptionTest(TestCase):
    def test_inscription_candidat(self):
        c = Client()
        response = c.post(reverse('inscription'), {
            'nom': 'Dupont',
            'prenom': 'Jean',
            'email': 'jean@test.com',
            'password': 'Test1234!',
            'role': 'candidat',
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Utilisateur.objects.filter(email='jean@test.com').exists())

    def test_inscription_recruteur(self):
        c = Client()
        response = c.post(reverse('inscription'), {
            'nom': 'Martin',
            'prenom': 'Sophie',
            'email': 'sophie@test.com',
            'password': 'Test1234!',
            'role': 'recruteur',
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Utilisateur.objects.filter(email='sophie@test.com').exists())


class ConnexionTest(TestCase):
    def setUp(self):
        self.user = Utilisateur.objects.create_user(
            username='test@test.com',
            email='test@test.com',
            password='Test1234!',
            nom='Test',
            prenom='User',
            role='candidat'
        )
        Candidat.objects.create(utilisateur=self.user)

    def test_connexion_valide(self):
        c = Client()
        response = c.post(reverse('connexion'), {
            'email': 'test@test.com',
            'password': 'Test1234!',
        })
        self.assertEqual(response.status_code, 302)

    def test_connexion_invalide(self):
        c = Client()
        response = c.post(reverse('connexion'), {
            'email': 'test@test.com',
            'password': 'mauvais',
        })
        self.assertEqual(response.status_code, 302)


class OffreTest(TestCase):
    def setUp(self):
        self.recruteur_user = Utilisateur.objects.create_user(
            username='recruteur@test.com',
            email='recruteur@test.com',
            password='Test1234!',
            nom='Recruteur',
            prenom='Test',
            role='recruteur'
        )
        self.recruteur = Recruteur.objects.create(
            utilisateur=self.recruteur_user,
            entreprise='Test Inc',
            telephone='0123456789',
            departement='IT'
        )

    def test_creation_offre(self):
        offre = Offre.objects.create(
            titre='Developpeur Python',
            description='Description du poste',
            lieu='Paris',
            type_contrat='CDI',
            recruteur=self.recruteur
        )
        self.assertEqual(offre.titre, 'Developpeur Python')
        self.assertEqual(offre.type_contrat, 'CDI')

    def test_liste_offres_publique(self):
        c = Client()
        response = c.get(reverse('liste_offres'))
        self.assertEqual(response.status_code, 200)


class ModeleTest(TestCase):
    def test_utilisateur_str(self):
        user = Utilisateur.objects.create_user(
            username='test@test.com',
            email='test@test.com',
            password='Test1234!',
            nom='Dupont',
            prenom='Jean',
            role='candidat'
        )
        self.assertEqual(str(user), 'Jean Dupont')
