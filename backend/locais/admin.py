from django.contrib import admin

from .models import TipoAbrigo

admin.site.site_header = 'ALERA · Painel da Defesa Civil (Demonstração)'
admin.site.site_title = 'ALERA · Demonstração'
admin.site.index_title = 'Demonstração: não é um sistema oficial da Defesa Civil'

# Ficam fora do /admin/: áreas de risco e abrigos (o painel ALERA desenha no mapa e
# emite os alertas), bairros (nascem sozinhos pelo CEP) e ruas (não são mais usadas)


@admin.register(TipoAbrigo)
class TipoAbrigoAdmin(admin.ModelAdmin):
    list_display = ['nome', 'icone']
    search_fields = ['nome']
