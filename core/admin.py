from django.contrib import admin
from .models import PerfilUsuario, Talhao, Plantio, Manejo, Irrigacao, Ocorrencia

admin.site.register(PerfilUsuario)
admin.site.register(Talhao)
admin.site.register(Plantio)
admin.site.register(Manejo)
admin.site.register(Irrigacao)
admin.site.register(Ocorrencia)
