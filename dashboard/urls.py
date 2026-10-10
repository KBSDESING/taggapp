
from django.urls import path
from . import views

urlpatterns = [
    path('', views.tableau_de_bord, name='tableau_de_bord'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('export-csv/', views.export_csv, name='export_csv'),
    path('groupes/', views.former_groupes, name='former_groupes'),
    path('alertes/sans-seance/', views.alerte_sans_seance, name='alerte_sans_seance'),
    path('alertes/sans-progres/', views.alerte_sans_progres, name='alerte_sans_progres'),
    path('alertes/taux-baisse/', views.alerte_taux_baisse, name='alerte_taux_baisse'),
    path('api/enfants/', views.api_enfants, name='api_enfants'),
    path('api/enfants/<int:pk>/', views.api_enfant_detail, name='api_enfant_detail'),
    path('api/seances/', views.api_seance, name='api_seance'),
    path('api/login/', views.api_login, name='api_login'),
    path('api/enfants/creer/', views.api_creer_enfant, name='api_creer_enfant'),
    path('api/enfants/<int:pk>/niveau/', views.api_mettre_a_jour_niveau, name='api_mettre_a_jour_niveau'),
    path('api/facilitateur/<int:facilitateur_id>/enfants/', views.api_enfants_facilitateur, name='api_enfants_facilitateur'),

]