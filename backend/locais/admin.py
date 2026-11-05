from django.contrib import admin

from .models import AreaRisco, TipoAbrigo

admin.site.site_header = 'ALERA · Painel da Defesa Civil (Demonstração)'
admin.site.site_title = 'ALERA · Demonstração'
admin.site.index_title = 'Demonstração: não é um sistema oficial da Defesa Civil'

# Abrigos, bairros e ruas ficam fora do /admin/: abrigo é trabalho do ADMzinho no
# painel ALERA, bairro nasce sozinho pelo CEP do morador e rua não é mais usada


@admin.register(AreaRisco)
class AreaRiscoAdmin(admin.ModelAdmin):
    list_display = ['nome', 'nivel', 'nivel_atualizado_em']
    list_filter = ['nivel']
    search_fields = ['nome']
    # O ADMzão cria a área e muda o nome. O nível muda pelo painel ALERA ou pela
    # previsão, sempre por alertas.servicos.mudar_nivel, que grava o histórico
    readonly_fields = ['nivel', 'nivel_atualizado_em']


@admin.register(TipoAbrigo)
class TipoAbrigoAdmin(admin.ModelAdmin):
    list_display = ['nome', 'icone']
    search_fields = ['nome']
