from django.contrib import admin

from .models import Missao, MissaoConcluida, RelatoLixo


@admin.register(Missao)
class MissaoAdmin(admin.ModelAdmin):
    list_display = ['titulo', 'pontos', 'ordem', 'ativa']
    list_filter = ['ativa']


@admin.register(MissaoConcluida)
class MissaoConcluidaAdmin(admin.ModelAdmin):
    list_display = ['morador', 'missao', 'pontos', 'concluida_em']
    list_filter = ['missao']
    search_fields = ['morador__email']
    raw_id_fields = ['morador']


@admin.register(RelatoLixo)
class RelatoLixoAdmin(admin.ModelAdmin):
    list_display = ['local', 'criado_em']
    search_fields = ['local', 'descricao']
    raw_id_fields = ['morador']
