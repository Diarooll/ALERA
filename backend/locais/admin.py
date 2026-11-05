from django.contrib import admin

from alertas.models import HistoricoNivel
from alertas.servicos import mudar_nivel

from .models import Abrigo, AreaRisco, Rua

admin.site.site_header = 'ALERA · Painel da Defesa Civil (Demonstração)'
admin.site.site_title = 'ALERA · Demonstração'
admin.site.index_title = 'Demonstração: não é um sistema oficial da Defesa Civil'


@admin.register(AreaRisco)
class AreaRiscoAdmin(admin.ModelAdmin):
    list_display = ['nome', 'nivel', 'nivel_atualizado_em']
    list_filter = ['nivel']
    search_fields = ['nome']
    readonly_fields = ['nivel_atualizado_em']

    def get_readonly_fields(self, request, obj=None):
        # Área nova começa em Normal: o nível só muda depois, com registro no histórico
        return self.readonly_fields if obj else [*self.readonly_fields, 'nivel']

    def save_model(self, request, obj, form, change):
        novo_nivel = obj.nivel
        mudou_nivel = change and 'nivel' in form.changed_data
        if mudou_nivel:
            obj.nivel = form.initial['nivel']

        super().save_model(request, obj, form, change)

        if mudou_nivel:
            mudar_nivel(obj, novo_nivel, HistoricoNivel.Origem.DEFESA_CIVIL, request.user)
            obj.refresh_from_db()


@admin.register(Rua)
class RuaAdmin(admin.ModelAdmin):
    list_display = ['nome', 'bairro', 'area']
    list_filter = ['area', 'bairro']
    search_fields = ['nome', 'bairro']


@admin.register(Abrigo)
class AbrigoAdmin(admin.ModelAdmin):
    list_display = ['nome', 'area', 'situacao', 'distancia_m', 'tempo_a_pe_min']
    list_filter = ['area', 'situacao']
    search_fields = ['nome']
