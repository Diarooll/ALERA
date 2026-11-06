from django.core.management.base import BaseCommand

from locais.models import Abrigo, AreaRisco, CirculoRisco, TipoAbrigo

AREA = 'Área de Risco Exemplo'
# Bolinhas de exemplo no centro de Juiz de Fora: (latitude, longitude, raio em metros)
BOLINHAS = [
    ('-21.764200', '-43.350300', 400),
    ('-21.767500', '-43.346500', 300),
]
# Nomes e posições de exemplo: não são abrigos reais. Ficam fora das bolinhas
ABRIGOS = [
    ('Escola Municipal Exemplo', 'Escola', 'aberto', '-21.758000', '-43.356000', 300),
    ('Igreja Exemplo', 'Igreja', 'poucas', '-21.773000', '-43.357000', 80),
    ('Ginásio Exemplo', 'Ginásio/quadra', 'so-alerta', '-21.759000', '-43.340000', 500),
    ('Centro Comunitário Exemplo', 'Centro comunitário', 'aberto', '-21.774000', '-43.338000', 150),
]


class Command(BaseCommand):
    help = 'Cria dados de exemplo (uma área com bolinhas e abrigos em Juiz de Fora). Pode rodar de novo.'

    def handle(self, *args, **opcoes):
        area, _ = AreaRisco.objects.get_or_create(nome=AREA)
        if not area.circulos.exists():
            CirculoRisco.objects.bulk_create(
                CirculoRisco(area=area, latitude=lat, longitude=lng, raio_m=raio)
                for lat, lng, raio in BOLINHAS
            )

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
