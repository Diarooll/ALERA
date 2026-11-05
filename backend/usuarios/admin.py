from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Usuario


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    """No /admin/ o ADMzão só cuida de contas de ADM. Morador não aparece aqui."""

    ordering = ['email']
    list_display = ['email', 'is_superuser', 'is_active', 'last_login']
    list_filter = ['is_superuser', 'is_active']
    search_fields = ['email']
    readonly_fields = ['last_login', 'date_joined']
    # Sem os dados de morador (endereço, bairro, consentimento) e sem is_staff:
    # pelo /admin/ ninguém vira morador, só dá para promover a ADMzão
    fieldsets = [
        (None, {'fields': ['email', 'password']}),
        ('Permissões', {'fields': ['is_active', 'is_superuser']}),
        ('Datas', {'fields': ['last_login', 'date_joined']}),
    ]
    add_fieldsets = [
        (None, {'classes': ['wide'], 'fields': ['email', 'usable_password', 'password1', 'password2']}),
    ]

    def get_queryset(self, request):
        # Esconde os moradores da lista e também da edição direta pelo endereço
        return super().get_queryset(request).filter(is_staff=True)

    def save_model(self, request, obj, form, change):
        # Toda conta daqui é de ADM: nasce ADMzinho e nunca volta a ser morador
        obj.is_staff = True
        super().save_model(request, obj, form, change)
