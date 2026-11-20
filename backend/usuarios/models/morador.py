from .usuario import Usuario


class Morador(Usuario):
    """Os moradores, que no /admin/ aparecem como "Usuários": só leitura e sem dado sensível.

    O nome aparece como "Morador nº 12" para o e-mail não vazar nos títulos e caminhos
    das páginas do admin.
    """

    class Meta:
        proxy = True
        verbose_name = 'usuário'
        verbose_name_plural = 'usuários'

    def __str__(self):
        return f'Morador nº {self.pk}'
