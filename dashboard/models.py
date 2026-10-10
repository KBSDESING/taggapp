from django.db import models
from django.contrib.auth.models import User

class Enfant(models.Model):
    prenom = models.CharField(max_length=100)
    famille = models.CharField(max_length=100)
    facilitateur = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='enfants'
    )
    niveau_lecture = models.IntegerField(default=1)
    niveau_calcul = models.IntegerField(default=1)
    niveau_lecture_depart = models.IntegerField(default=1)
    niveau_calcul_depart = models.IntegerField(default=1)
    date_inscription = models.DateField(auto_now_add=True)
    def __str__(self):
        return self.prenom
class Seance(models.Model):
    enfant = models.ForeignKey(Enfant, on_delete=models.CASCADE)
    date = models.DateTimeField(auto_now_add=True)
    nb_bonnes_reponses = models.IntegerField(default=0)
    nb_total_questions = models.IntegerField(default=10)
    type_exercice = models.CharField(
        max_length=20,
        choices=[('lecture', 'Lecture'), ('calcul', 'Calcul')]
    )
    def __str__(self):
        return f"{self.enfant.prenom} — {self.date}"
