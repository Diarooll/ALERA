from django.contrib import admin

from .models import HistoricoNivel, Previsao


class SomenteLeitura(admin.ModelAdmin):
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Previsao)
class PrevisaoAdmin(SomenteLeitura):
    list_display = ['area', 'chuva_mm_24h', 'nivel_calculado', 'fonte', 'recebida_em']
    list_filter = ['area', 'nivel_calculado']


@admin.register(HistoricoNivel)
class HistoricoNivelAdmin(SomenteLeitura):
    list_display = ['criado_em', 'area', 'nivel_anterior', 'nivel_novo', 'origem', 'responsavel']
    list_filter = ['area', 'origem', 'nivel_novo']
