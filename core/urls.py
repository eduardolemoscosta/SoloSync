from django.urls import path
from . import views

urlpatterns = [
    path('', views.DashboardView.as_view(), name='dashboard'),
    path('signup/', views.signup, name='signup'),
    
    path('talhoes/', views.TalhaoListView.as_view(), name='talhao_list'),
    path('talhoes/novo/', views.TalhaoCreateView.as_view(), name='talhao_create'),
    path('talhoes/<int:pk>/editar/', views.TalhaoUpdateView.as_view(), name='talhao_update'),
    path('talhoes/<int:pk>/excluir/', views.TalhaoDeleteView.as_view(), name='talhao_delete'),
    
    path('plantios/', views.PlantioListView.as_view(), name='plantio_list'),
    path('plantios/novo/', views.PlantioCreateView.as_view(), name='plantio_create'),
    path('plantios/<int:pk>/', views.PlantioDetailView.as_view(), name='plantio_detail'),
    path('plantios/<int:pk>/editar/', views.PlantioUpdateView.as_view(), name='plantio_update'),
    path('plantios/<int:pk>/excluir/', views.PlantioDeleteView.as_view(), name='plantio_delete'),
    
    path('manejos/novo/', views.ManejoCreateView.as_view(), name='manejo_create'),
    path('irrigacoes/nova/', views.IrrigacaoCreateView.as_view(), name='irrigacao_create'),
    path('ocorrencias/nova/', views.OcorrenciaCreateView.as_view(), name='ocorrencia_create'),
]
