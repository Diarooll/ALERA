from .usuario import Usuario


# No /admin/ as contas aparecem em duas seções. As duas são a mesma tabela de Usuario.


class Staff(Usuario):
    """Contas de ADM (ADMzão e ADMzinho)."""

    class Meta:
        proxy = True
        verbose_name = 'staff'
        verbose_name_plural = 'staffs'
