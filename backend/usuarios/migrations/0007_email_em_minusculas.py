from collections import defaultdict

from django.db import migrations


def passar_emails_para_minusculas(apps, schema_editor):
    """Contas antigas criadas no /admin/ com maiúscula ("Ana@...") não entravam pelo app.

    Vem antes da regra de e-mail único sem caixa (migração seguinte), que exige isto pronto.
    """
    Usuario = apps.get_model('usuarios', 'Usuario')
    contas = list(Usuario.objects.values_list('pk', 'email'))

    por_email = defaultdict(list)
    for pk, email in contas:
        por_email[email.strip().lower()].append(pk)

    repetidas = [pks for pks in por_email.values() if len(pks) > 1]
    if repetidas:
        # Não dá para escolher sozinho qual conta fica: alguém precisa decidir.
        # Só os números das contas aparecem, nunca o e-mail
        grupos = '; '.join(', '.join(f'nº {pk}' for pk in pks) for pks in repetidas)
        raise RuntimeError(
            f'Há contas com o mesmo e-mail escrito com maiúsculas diferentes ({grupos}). '
            'Apague uma delas ou troque o e-mail pelo "manage.py shell" e rode o migrate de novo.'
        )

    for pk, email in contas:
        normalizado = email.strip().lower()
        if email != normalizado:
            Usuario.objects.filter(pk=pk).update(email=normalizado)


class Migration(migrations.Migration):

    dependencies = [
        ('usuarios', '0006_complemento_do_endereco'),
    ]

    operations = [
        migrations.RunPython(passar_emails_para_minusculas, migrations.RunPython.noop),
    ]
