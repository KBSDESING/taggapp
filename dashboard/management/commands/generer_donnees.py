from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from dashboard.models import Enfant, Seance
from datetime import timedelta
from django.utils import timezone
import random

class Command(BaseCommand):
    help = 'Génère des données de démonstration'
    def handle(self, *args, **kwargs):
        # Supprimer anciennes données
        Seance.objects.all().delete()
        Enfant.objects.all().delete()
        self.stdout.write('🗑️  Anciennes données supprimées')
        # Récupérer les facilitateurs
        try:
            keba = User.objects.get(username='admin')
        except User.DoesNotExist:
            keba = User.objects.first()
        try:
            mamadou = User.objects.get(username='mamadou')
        except User.DoesNotExist:
            mamadou = keba
        facilitateurs = [keba, mamadou]
        # Noms sénégalais
        prenoms = [
            "Awa", "Modou", "Fatou", "Ibrahima", "Khady",
            "Mamadou", "Aissatou", "Ousmane", "Mariama", "Cheikh",
            "Ndéye", "Abdoulaye", "Rokhaya", "Moussa", "Adja",
            "Seydou", "Coumba", "Lamine", "Sokhna", "Babacar",
            "Penda", "Alioune", "Astou", "Demba", "Dieynaba",
            "Samba", "Aminata", "Malick", "Yacine", "Binta"
        ]
        familles = [
            "Diallo", "Ndiaye", "Sow", "Fall", "Ba",
            "Diop", "Sylla", "Mbaye", "Thiaw", "Sarr"
        ]
        # Créer 30 enfants
        maintenant = timezone.now()
        enfants = []
        for i in range(30):
            niveau_dep = random.randint(1, 3)
            enfant = Enfant.objects.create(
                prenom=prenoms[i],
                famille=random.choice(familles),
                facilitateur=random.choice(facilitateurs),
                niveau_lecture=niveau_dep,
                niveau_calcul=niveau_dep,
                niveau_lecture_depart=niveau_dep,
                niveau_calcul_depart=niveau_dep,
            )
            enfants.append(enfant)
        self.stdout.write(f'👦 30 enfants créés')
        # Créer des séances
        nb_total = 0
        for enfant in enfants:
            nb_seances = random.randint(2, 15)
            for j in range(nb_seances):
                jours = random.randint(0, 30)
                Seance.objects.create(
                    enfant=enfant,
                    date=maintenant - timedelta(days=jours),
                    nb_bonnes_reponses=random.randint(3, 10),
                    nb_total_questions=10,
                    type_exercice=random.choice(
                        ['lecture', 'calcul']
                    )
                )
                nb_total += 1
            # Faire progresser certains enfants
            if nb_seances >= 8 and random.random() > 0.5:
                enfant.niveau_lecture = min(
                    enfant.niveau_lecture + 1, 5
                )
                enfant.niveau_calcul = min(
                    enfant.niveau_calcul + 1, 5
                )
                enfant.save()
        self.stdout.write(f'📚 {nb_total} séances créées')
        self.stdout.write('✅ Données générées avec succès !')
