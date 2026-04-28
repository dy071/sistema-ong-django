from django.contrib import admin
from .models import Material, Movimentacao

# Painel para material
@admin.register(Material)
class MaterialAdmin(admin.ModelAdmin):
    list_display = ('nome', 'categoria', 'estoque_real', 'estado', 'data_cadastro')
    search_fields = ('nome',)
    list_filter = ('categoria', 'estado')

    # Função para a atualização do estoque
    def estoque_real(self, obj):
        return obj.estoque_atual()
    
    estoque_real.short_description = "Estoque"

# Painel para movimentacao
@admin.register(Movimentacao)
class MovimentacaoAdmin(admin.ModelAdmin):
    list_display = ('material', 'tipo', 'quantidade', 'data')