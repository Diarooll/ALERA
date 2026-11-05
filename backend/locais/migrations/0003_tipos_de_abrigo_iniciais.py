from django.db import migrations

# Dado de referência: os tipos de abrigo que o admin escolhe ao marcar o pin no mapa.
# O admin cria outros pelo painel ou pelo Django admin.
TIPOS = [
    {'nome': 'Escola', 'icone': '🏫'},
    {'nome': 'Igreja', 'icone': '⛪'},
    {'nome': 'Ginásio/quadra', 'icone': '🏟️'},
    {'nome': 'Centro comunitário', 'icone': '🏘️'},
    {'nome': 'Outro', 'icone': '📍'},
]


def criar_tipos(apps, schema_editor):
    TipoAbrigo = apps.get_model('locais', 'TipoAbrigo')
    for tipo in TIPOS:
        TipoAbrigo.objects.get_or_create(nome=tipo['nome'], defaults={'icone': tipo['icone']})


def remover_tipos(apps, schema_editor):
    apps.get_model('locais', 'TipoAbrigo').objects.filter(
        nome__in=[t['nome'] for t in TIPOS], abrigos__isnull=True
    ).delete()


class Migration(migrations.Migration):
    dependencies = [('locais', '0002_tipoabrigo_alter_abrigo_options_abrigo_capacidade_and_more')]

    operations = [migrations.RunPython(criar_tipos, remover_tipos)]
