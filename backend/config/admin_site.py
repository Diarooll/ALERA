from django.contrib.admin import AdminSite
from django.contrib.admin.forms import AdminAuthenticationForm
from django.core.exceptions import ValidationError
from django.http import HttpResponse
from rest_framework.throttling import SimpleRateThrottle


class LimiteDoLoginDoAdmin(SimpleRateThrottle):
    """O mesmo limite do login da API (10 por minuto), contado à parte, por IP."""

    scope = 'login'

    def get_cache_key(self, request, view):
        return self.cache_format % {'scope': 'admin-login', 'ident': self.get_ident(request)}


class LoginDoAdmPrincipal(AdminAuthenticationForm):
    """A tela de login do /admin/ recusa quem não é ADM principal, sem abrir sessão."""

    def confirm_login_allowed(self, user):
        super().confirm_login_allowed(user)
        if not user.is_superuser:
            raise ValidationError(
                self.error_messages['invalid_login'],
                code='invalid_login',
                params={'username': self.username_field.verbose_name},
            )


class AleraAdminSite(AdminSite):
    """O /admin/ é só do ADM principal. O ADMzinho usa o painel próprio."""

    login_form = LoginDoAdmPrincipal

    def login(self, request, extra_context=None):
        # Sem limite, a senha do ADM principal podia ser chutada sem parar por aqui.
        # Só tentar entrar (POST) conta; abrir a tela não conta
        if request.method == 'POST' and not LimiteDoLoginDoAdmin().allow_request(request, None):
            return HttpResponse(
                'Muitas tentativas. Aguarde um minuto e tente de novo.',
                status=429,
                content_type='text/plain; charset=utf-8',
            )
        return super().login(request, extra_context)

    def has_permission(self, request):
        return super().has_permission(request) and request.user.is_superuser
