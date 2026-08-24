from django.contrib import admin
from .models import Propriedade, Talhao, Plantio, Manejo, Irrigacao, Ocorrencia, PerfilUsuario

class PropriedadeAdmin(admin.ModelAdmin):
    list_display = ('nome', 'usuario', 'cidade', 'estado', 'area_total_ha', 'criado_em')
    list_filter = ('estado', 'criado_em')
    search_fields = ('nome', 'cidade', 'usuario__username')

class TalhaoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'propriedade', 'area_m2', 'tipo_solo', 'ativo', 'criado_em')
    list_filter = ('ativo', 'tipo_solo', 'propriedade')
    search_fields = ('nome', 'propriedade__nome', 'propriedade__usuario__username')

admin.site.register(Propriedade, PropriedadeAdmin)
admin.site.register(Talhao, TalhaoAdmin)
admin.site.register(Plantio)
admin.site.register(Manejo)
admin.site.register(Irrigacao)
admin.site.register(Ocorrencia)
admin.site.register(PerfilUsuario)

