from django.db import migrations

# As mesmas quatro missões e pontos do site e do app
MISSOES = [
    {
        'codigo': 'limpe-bueiro',
        'titulo': 'Limpe o bueiro',
        'descricao': 'Tire o lixo da frente do bueiro. Com a água subindo, não chegue perto: ligue 199.',
        'pontos': 50,
        'ordem': 1,
    },
    {
        'codigo': 'reporte-lixo',
        'titulo': 'Reporte lixo',
        'descricao': 'Conte onde há lixo acumulado na sua rua.',
        'pontos': 20,
        'ordem': 2,
    },
    {
        'codigo': 'plante-muda',
        'titulo': 'Plante uma muda',
        'descricao': 'Plante uma muda na encosta, somente em local autorizado.',
        'pontos': 80,
        'ordem': 3,
    },
    {
        'codigo': 'salve-abrigo',
        'titulo': 'Salve seu abrigo',
        'descricao': 'Escolha o abrigo mais próximo e salve no app.',
        'pontos': 10,
        'ordem': 4,
    },
]


def criar_missoes(apps, schema_editor):
    Missao = apps.get_model('missoes', 'Missao')
    for missao in MISSOES:
        Missao.objects.create(**missao)


def remover_missoes(apps, schema_editor):
    Missao = apps.get_model('missoes', 'Missao')
    Missao.objects.filter(codigo__in=[missao['codigo'] for missao in MISSOES]).delete()


class Migration(migrations.Migration):
    dependencies = [('missoes', '0001_initial')]

    operations = [migrations.RunPython(criar_missoes, remover_missoes)]
