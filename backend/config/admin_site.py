from django.contrib.admin import AdminSite
from django.contrib.admin.forms import AdminAuthenticationForm
from django.core.exceptions import ValidationError


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

    def has_permission(self, request):
        return super().has_permission(request) and request.user.is_superuser
