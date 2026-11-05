from django.core.management.base import BaseCommand

from locais.models import Abrigo, AreaRisco, Bairro, TipoAbrigo

CIDADE = 'Juiz de Fora'
AREA = 'Área de Risco Exemplo'
# Só os bairros de exemplo entram na área; os outros nascem sem área, como no cadastro real
BAIRROS_NA_AREA = ['Centro', 'São Mateus']
# Nomes e posições de exemplo: não são abrigos reais
ABRIGOS = [
    ('Escola Municipal Exemplo', 'Escola', 'aberto', '-21.762000', '-43.348000', 300),
    ('Igreja Exemplo', 'Igreja', 'poucas', '-21.768000', '-43.355000', 80),
    ('Ginásio Exemplo', 'Ginásio/quadra', 'so-alerta', '-21.759000', '-43.343000', 500),
    ('Centro Comunitário Exemplo', 'Centro comunitário', 'aberto', '-21.772000', '-43.338000', 150),
]


class Command(BaseCommand):
    help = 'Cria dados de exemplo (uma área, bairros e abrigos em Juiz de Fora). Pode rodar de novo.'

    def handle(self, *args, **opcoes):
        area, _ = AreaRisco.objects.get_or_create(nome=AREA)

        for nome in BAIRROS_NA_AREA:
            bairro, _ = Bairro.objects.get_or_create(nome=nome, cidade=CIDADE)
            if bairro.area_id is None:
                bairro.area = area
                bairro.save(update_fields=['area'])

        for nome, tipo, situacao, lat, lng, vagas in ABRIGOS:
            Abrigo.objects.get_or_create(
                nome=nome,
                defaults={
                    'tipo': TipoAbrigo.objects.get(nome=tipo),
                    'situacao': situacao,
                    'latitude': lat,
                    'longitude': lng,
                    'capacidade': vagas,
                },
            )

        self.stdout.write(self.style.SUCCESS('Dados de exemplo prontos.'))
