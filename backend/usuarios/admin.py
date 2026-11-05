from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Usuario


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    ordering = ['email']
    list_display = ['email', 'telefone', 'bairro', 'is_staff', 'is_active']
    search_fields = ['email', 'telefone']
    readonly_fields = ['consentimento_em', 'consentimento_texto', 'last_login', 'date_joined']
    fieldsets = [
        (None, {'fields': ['email', 'password']}),
        # Latitude e longitude ficam de fora de propósito: ninguém vê onde o morador mora
        ('Contato', {'fields': ['telefone', 'endereco', 'cep', 'logradouro', 'numero', 'bairro', 'abrigo', 'alertas_ativos']}),
        ('Consentimento', {'fields': ['consentimento_em', 'consentimento_texto']}),
        ('Permissões', {'fields': ['is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions']}),
        ('Datas', {'fields': ['last_login', 'date_joined']}),
    ]
    add_fieldsets = [
        (None, {'classes': ['wide'], 'fields': ['email', 'usable_password', 'password1', 'password2']}),
    ]
