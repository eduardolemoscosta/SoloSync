from django.urls import path
from . import views

urlpatterns = [
    path('', views.DashboardView.as_view(), name='dashboard'),
    path('signup/', views.signup, name='signup'),
    path('configurar-propriedade/', views.configurar_propriedade, name='configurar_propriedade'),
    
    # Propriedades
    path('propriedades/', views.PropriedadeListView.as_view(), name='propriedade_list'),
    path('propriedades/nova/', views.PropriedadeCreateView.as_view(), name='propriedade_create'),
    path('propriedades/<int:pk>/editar/', views.PropriedadeUpdateView.as_view(), name='propriedade_update'),
    path('propriedades/<int:pk>/excluir/', views.PropriedadeDeleteView.as_view(), name='propriedade_delete'),
    
    path('talhoes/', views.TalhaoListView.as_view(), name='talhao_list'),
    path('talhoes/novo/', views.TalhaoCreateView.as_view(), name='talhao_create'),
    path('talhoes/<int:pk>/dashboard/', views.talhao_dashboard, name='talhao_dashboard'),
    path('talhoes/<int:pk>/editar/', views.TalhaoUpdateView.as_view(), name='talhao_update'),
    path('talhoes/<int:pk>/excluir/', views.TalhaoDeleteView.as_view(), name='talhao_delete'),
    
    path('talhoes/unir/', views.unir_talhoes, name='talhoes_unir'),
    path('talhoes/<int:pk>/dividir/', views.dividir_talhao, name='talhoes_dividir'),
    path('talhoes/dividir-mapa/', views.dividir_talhao_mapa, name='dividir_talhao_mapa'),
    
    path('plantios/', views.PlantioListView.as_view(), name='plantio_list'),
    path('plantios/novo/', views.PlantioCreateView.as_view(), name='plantio_create'),
    path('plantios/<int:pk>/', views.PlantioDetailView.as_view(), name='plantio_detail'),
    path('plantios/<int:pk>/editar/', views.PlantioUpdateView.as_view(), name='plantio_update'),
    path('plantios/<int:pk>/excluir/', views.PlantioDeleteView.as_view(), name='plantio_delete'),
    path('plantios/<int:pk>/colher/', views.registrar_colheita, name='plantio_colher'),
    
    path('manejos/novo/', views.ManejoCreateView.as_view(), name='manejo_create'),
    path('irrigacoes/nova/', views.IrrigacaoCreateView.as_view(), name='irrigacao_create'),
    path('ocorrencias/nova/', views.OcorrenciaCreateView.as_view(), name='ocorrencia_create'),
]
