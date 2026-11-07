import re

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group

from .models import Morador, Staff

# Grupos de permissão não são usados: o acesso vem de is_superuser (ADMzão) e is_staff (ADMzinho)
admin.site.unregister(Group)


@admin.register(Staff)
class StaffAdmin(UserAdmin):
    """Seção "Staffs": o ADMzão cria e cuida das contas de ADM. Morador não aparece aqui."""

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


@admin.register(Morador)
class MoradorAdmin(admin.ModelAdmin):
    """Moradores só para consulta: número da conta, telefone e data de cadastro.

    E-mail, senha, endereço, bairro, posição da casa e consentimento ficam de fora.
    O morador cuida da própria conta pelo app; aqui ninguém cria, muda ou apaga.
    """

    list_display = ['__str__', 'telefone_formatado', 'cadastrado_em']
    fields = ['telefone_formatado', 'cadastrado_em']
    readonly_fields = fields
    search_fields = ['telefone']
    ordering = ['-date_joined']
    actions = None

    def get_queryset(self, request):
        return super().get_queryset(request).filter(is_staff=False)

    def lookup_allowed(self, lookup, value, request):
        # Nenhum filtro pela barra de endereço. Sem isto, ?email__startswith=m ou
        # ?password__startswith=... mostrava quantos moradores batiam, e o ADMzão descobria
        # e-mail, endereço e até o hash da senha letra por letra. Fica só a busca por telefone
        return False

    def get_search_results(self, request, queryset, termo):
        # A busca aceita o telefone com ou sem pontuação: (32) 99999-0000
        return super().get_search_results(request, queryset, re.sub(r'\D', '', termo))

    @admin.display(description='telefone')
    def telefone_formatado(self, morador):
        digitos = morador.telefone
        if len(digitos) not in (10, 11):
            return digitos or '—'
        corte = 7 if len(digitos) == 11 else 6
        return f'({digitos[:2]}) {digitos[2:corte]}-{digitos[corte:]}'

    @admin.display(description='cadastrado em', ordering='date_joined')
    def cadastrado_em(self, morador):
        return morador.date_joined.strftime('%d/%m/%Y')

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
