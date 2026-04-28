from django.urls import path
from . import views

urlpatterns = [
    path('', views.lista_materiais, name='lista_materiais'),
    path('novo/', views.cadastrar_material, name='cadastrar_material'),
    path('editar/<int:id>/', views.editar_material, name='editar_material'),
    path('movimentacoes/', views.lista_movimentacoes, name='lista_movimentacoes'),
    path('movimentar/<int:id>/', views.cadastro_movimentacoes, name='cadastrar_movimentacao'),
       
    # Rota de exclusão (é ela que estava faltando ou com nome errado!)
    path('excluir/<int:id>/', views.excluir_material, name='excluir_material'),
]   