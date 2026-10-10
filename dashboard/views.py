
import csv
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.utils import timezone
from datetime import timedelta
from rest_framework.response import Response
from rest_framework.decorators import api_view
from .models import Enfant, Seance
from .serializers import EnfantSerializer, SeanceSerializer
# ═══════════════════════════════
# FONCTION PARTAGÉE
# ═══════════════════════════════
def calculer_taux_baisse(enfants_qs):
    taux_baisse = []
    for enfant in enfants_qs:
        seances = Seance.objects.filter(
            enfant=enfant
        ).order_by('-date')[:5]
        if seances.count() >= 2:
            taux_list = []
            for s in seances:
                if s.nb_total_questions > 0:
                    taux = (
                        s.nb_bonnes_reponses / s.nb_total_questions
                    ) * 100
                    taux_list.append(round(taux, 1))
            if len(taux_list) >= 2:
                if taux_list[0] < taux_list[-1] - 10:
                    taux_baisse.append({
                        'enfant': enfant,
                        'taux_actuel': taux_list[0],
                        'taux_precedent': taux_list[-1]
                    })
    return taux_baisse
#  ═══════════════════════════════
# API - Autntification facilitateur
# ═══════════════════════════════
@api_view(['POST'])
def api_login(request):
    username = request.data.get('username')
    password = request.data.get('password')
    user = authenticate(username=username, password=password)
    if user:
        token, created = Token.objects.get_or_create(user=user)
        return Response({
            'status': 'success',
            'token': token.key,
            'user_id': user.id,
            'username': user.username,
            'message': f'Bienvenue {user.username} !'
        })
    else:
        return Response({
            'status': 'error',
            'message': 'Identifiants incorrects'
        })

# ═══════════════════════════════
# AUTHENTIFICATION
# ═══════════════════════════════
def login_view(request):
    if request.user.is_authenticated:
        return redirect('tableau_de_bord')
    error = None
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(
            request, username=username, password=password
        )
        if user is not None:
            login(request, user)
            return redirect('tableau_de_bord')
        else:
            error = "Nom d'utilisateur ou mot de passe incorrect"
    return render(request, 'dashboard/login.html', {'error': error})

def logout_view(request):
    logout(request)
    return redirect('login')
# ═══════════════════════════════
# TABLEAU DE BORD
# ═══════════════════════════════
@login_required(login_url='/login/')
def tableau_de_bord(request):
    # Filtrer selon le rôle
    if request.user.is_superuser:
        enfants_qs = Enfant.objects.all()
    else:
        enfants_qs = Enfant.objects.filter(
            facilitateur=request.user
        )
    # Recherche
    recherche = request.GET.get('q', '')
    if recherche:
        enfants_qs = enfants_qs.filter(
            prenom__icontains=recherche
        ) | enfants_qs.filter(
            famille__icontains=recherche
        ) | enfants_qs.filter(
            facilitateur__username__icontains=recherche
        )
    # Dates
    maintenant = timezone.now()
    il_y_a_3_jours = maintenant - timedelta(days=3)
    il_y_a_7_jours = maintenant - timedelta(days=7)
    # Calculs alertes
    sans_seance_3j = []
    sans_progres = []
    actifs_semaine = 0
    # Utiliser tous les enfants pour les alertes (pas la recherche)
    if request.user.is_superuser:
        tous_enfants = Enfant.objects.all()
    else:
        tous_enfants = Enfant.objects.filter(
            facilitateur=request.user
        )
    for enfant in tous_enfants:
        seances = Seance.objects.filter(enfant=enfant)
        derniere = seances.order_by('-date').first()
        # Actifs cette semaine
        if derniere and derniere.date >= il_y_a_7_jours:
            actifs_semaine += 1
        # Sans séance 3 jours
        if not derniere or derniere.date < il_y_a_3_jours:
            sans_seance_3j.append({
                'enfant': enfant,
                'derniere_seance': derniere.date if derniere else None
            })
        # Sans progrès
        nb_seances = seances.count()
        if nb_seances >= 10:
            if (enfant.niveau_lecture == enfant.niveau_lecture_depart
                    and enfant.niveau_calcul == enfant.niveau_calcul_depart):
                sans_progres.append(enfant)
    # Taux en baisse — fonction partagée
    taux_baisse = calculer_taux_baisse(tous_enfants)
    # Pagination sur la liste filtrée
    paginator = Paginator(enfants_qs, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'enfants': page_obj,
        'page_obj': page_obj,
        'total_enfants': tous_enfants.count(),
        'actifs_semaine': actifs_semaine,
        'sans_seance_3j': sans_seance_3j,
        'sans_progres': sans_progres,
        'taux_baisse': taux_baisse,
        'nb_alertes': len(sans_seance_3j) + len(sans_progres) + len(taux_baisse),
        'recherche': recherche,
    }
    return render(request, 'dashboard/tableau_de_bord.html', context)
# ═══════════════════════════════
# ALERTES
# ═══════════════════════════════
@login_required(login_url='/login/')
def alerte_sans_seance(request):
    if request.user.is_superuser:
        enfants_qs = Enfant.objects.all()
    else:
        enfants_qs = Enfant.objects.filter(
            facilitateur=request.user
        )
    maintenant = timezone.now()
    il_y_a_3_jours = maintenant - timedelta(days=3)
    sans_seance = []
    for enfant in enfants_qs:
        derniere = Seance.objects.filter(
            enfant=enfant
        ).order_by('-date').first()
        if not derniere or derniere.date < il_y_a_3_jours:
            sans_seance.append({
                'enfant': enfant,
                'derniere_seance': derniere.date if derniere else None,
                'nb_jours': (
                    maintenant - derniere.date
                ).days if derniere else None
            })
    # Recherche
    recherche = request.GET.get('q', '')
    if recherche:
        sans_seance = [
            item for item in sans_seance
            if recherche.lower() in item['enfant'].prenom.lower()
            or recherche.lower() in item['enfant'].famille.lower()
        ]
    paginator = Paginator(sans_seance, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'dashboard/alerte_sans_seance.html', {
        'sans_seance': page_obj,
        'page_obj': page_obj,
        'total': len(sans_seance),
        'recherche': recherche,
    })
@login_required(login_url='/login/')
def alerte_sans_progres(request):
    if request.user.is_superuser:
        enfants_qs = Enfant.objects.all()
    else:
        enfants_qs = Enfant.objects.filter(
            facilitateur=request.user
        )
    sans_progres = []
    for enfant in enfants_qs:
        nb_seances = Seance.objects.filter(enfant=enfant).count()
        if nb_seances >= 10:
            if (enfant.niveau_lecture == enfant.niveau_lecture_depart
                    and enfant.niveau_calcul == enfant.niveau_calcul_depart):
                sans_progres.append({
                    'enfant': enfant,
                    'nb_seances': nb_seances
                })
    # Recherche
    recherche = request.GET.get('q', '')
    if recherche:
        sans_progres = [
            item for item in sans_progres
            if recherche.lower() in item['enfant'].prenom.lower()
            or recherche.lower() in item['enfant'].famille.lower()
        ]
    paginator = Paginator(sans_progres, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'dashboard/alerte_sans_progres.html', {
        'sans_progres': page_obj,
        'page_obj': page_obj,
        'total': len(sans_progres),
        'recherche': recherche,
    })
@login_required(login_url='/login/')
def alerte_taux_baisse(request):
    if request.user.is_superuser:
        enfants_qs = Enfant.objects.all()
    else:
        enfants_qs = Enfant.objects.filter(
            facilitateur=request.user
        )
    # Utiliser la fonction partagée
    taux_baisse = calculer_taux_baisse(enfants_qs)
    # Recherche
    recherche = request.GET.get('q', '')
    if recherche:
        taux_baisse = [
            item for item in taux_baisse
            if recherche.lower() in item['enfant'].prenom.lower()
            or recherche.lower() in item['enfant'].famille.lower()
        ]
    paginator = Paginator(taux_baisse, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'dashboard/alerte_taux_baisse.html', {
        'taux_baisse': page_obj,
        'page_obj': page_obj,
        'total': len(taux_baisse),
        'recherche': recherche,
    })
# ═══════════════════════════════
# GROUPES & CSV
# ═══════════════════════════════
@login_required(login_url='/login/')
def former_groupes(request):
    if request.user.is_superuser:
        enfants = Enfant.objects.all()
    else:
        enfants = Enfant.objects.filter(
            facilitateur=request.user
        )
    type_groupe = request.GET.get('type', 'lecture')
    groupes = {}
    for enfant in enfants:
        niveau = enfant.niveau_lecture if type_groupe == 'lecture' \
            else enfant.niveau_calcul
        if niveau not in groupes:
            groupes[niveau] = []
        groupes[niveau].append(enfant)
    groupes_tries = dict(sorted(groupes.items()))
    return render(request, 'dashboard/groupes.html', {
        'groupes': groupes_tries,
        'type_groupe': type_groupe,
    })
@login_required(login_url='/login/')
def export_csv(request):
    if request.user.is_superuser:
        enfants_list = Enfant.objects.all()
    else:
        enfants_list = Enfant.objects.filter(
            facilitateur=request.user
        )
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = \
        'attachment; filename="enfants_taggapp.csv"'
    writer = csv.writer(response)
    writer.writerow([
        'Prénom', 'Famille', 'Facilitateur',
        'Niveau Lecture', 'Niveau Calcul',
        'Niveau Lecture Départ', 'Niveau Calcul Départ',
        'Date Inscription', 'Nb Séances', 'Dernière Séance'
    ])
    for enfant in enfants_list:
        nb_seances = Seance.objects.filter(enfant=enfant).count()
        derniere = Seance.objects.filter(
            enfant=enfant
        ).order_by('-date').first()
        derniere_date = derniere.date.strftime(
            '%d/%m/%Y'
        ) if derniere else 'Aucune'
        facilitateur_nom = enfant.facilitateur.get_full_name() \
            or enfant.facilitateur.username \
            if enfant.facilitateur else '—'
        writer.writerow([
            enfant.prenom, enfant.famille, facilitateur_nom,
            f'Niveau {enfant.niveau_lecture}',
            f'Niveau {enfant.niveau_calcul}',
            f'Niveau {enfant.niveau_lecture_depart}',
            f'Niveau {enfant.niveau_calcul_depart}',
            enfant.date_inscription.strftime('%d/%m/%Y'),
            nb_seances, derniere_date
        ])
    return response
# ═══════════════════════════════
# API REST
# ═══════════════════════════════
@api_view(['GET'])
def api_enfants(request):
    enfants = Enfant.objects.all()
    serializer = EnfantSerializer(enfants, many=True)
    return Response(serializer.data)
@api_view(['GET'])
def api_enfant_detail(request, pk):
    try:
        enfant = Enfant.objects.get(pk=pk)
        serializer = EnfantSerializer(enfant)
        return Response(serializer.data)
    except Enfant.DoesNotExist:
        return Response({
            'status': 'error',
            'message': 'Enfant introuvable'
        })
@api_view(['POST'])
def api_seance(request):
    serializer = SeanceSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response({
            'status': 'success',
            'message': 'Séance enregistrée !'
        })
    return Response({
        'status': 'error',
        'errors': serializer.errors
    })

# API — Enfants d'un facilitateur spécifique
@api_view(['GET'])
def api_enfants_facilitateur(request, facilitateur_id):
    enfants = Enfant.objects.filter(
        facilitateur_id=facilitateur_id
    )
    serializer = EnfantSerializer(enfants, many=True)
    return Response(serializer.data)

# API — Créer un enfant depuis le mobile
@api_view(['POST'])
def api_creer_enfant(request):
    serializer = EnfantSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response({
            'status': 'success',
            'message': 'Enfant créé !',
            'enfant': serializer.data
        })
    return Response({
        'status': 'error',
        'errors': serializer.errors
    })
# API — Mettre à jour le niveau d'un enfant
@api_view(['PUT'])
def api_mettre_a_jour_niveau(request, pk):
    try:
        enfant = Enfant.objects.get(pk=pk)
        enfant.niveau_lecture = request.data.get(
            'niveau_lecture', enfant.niveau_lecture
        )
        enfant.niveau_calcul = request.data.get(
            'niveau_calcul', enfant.niveau_calcul
        )
        enfant.save()
        return Response({
            'status': 'success',
            'message': 'Niveau mis à jour !',
            'niveau_lecture': enfant.niveau_lecture,
            'niveau_calcul': enfant.niveau_calcul
        })
    except Enfant.DoesNotExist:
        return Response({
            'status': 'error',
            'message': 'Enfant introuvable'
        })
