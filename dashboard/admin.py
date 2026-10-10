from django.contrib import admin
from .models import Enfant,Seance

# Register your models here.

@admin.register(Enfant)
class EnfantAdmin(admin.ModelAdmin):
    list_display = [
        'prenom', 'famille', 'facilitateur',
        'niveau_lecture', 'niveau_calcul',
        'date_inscription'
    ]
    list_filter = ['facilitateur', 'niveau_lecture', 'niveau_calcul']
    search_fields = ['prenom', 'famille']
    ordering = ['prenom']
    
@admin.register(Seance)
class SeanceAdmin(admin.ModelAdmin):
    list_display = [
        'enfant', 'type_exercice',
        'nb_bonnes_reponses', 'nb_total_questions', 'date'
    ]
    list_filter = ['type_exercice', 'date']
    search_fields = ['enfant__prenom']
    ordering = ['-date']
