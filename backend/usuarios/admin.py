from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Usuario


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    ordering = ['email']
    list_display = ['email', 'telefone', 'is_staff', 'is_active']
    search_fields = ['email', 'telefone']
    readonly_fields = ['consentimento_em', 'consentimento_texto', 'last_login', 'date_joined']
    fieldsets = [
        (None, {'fields': ['email', 'password']}),
        ('Contato', {'fields': ['telefone', 'endereco']}),
        ('Consentimento', {'fields': ['consentimento_em', 'consentimento_texto']}),
        ('Permissões', {'fields': ['is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions']}),
        ('Datas', {'fields': ['last_login', 'date_joined']}),
    ]
    add_fieldsets = [
        (None, {'classes': ['wide'], 'fields': ['email', 'usable_password', 'password1', 'password2']}),
    ]
