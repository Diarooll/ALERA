from django.db import IntegrityError, transaction

from locais.models import Nivel

from ..models import HistoricoNivel, Previsao
from .base import DEFESA_CIVIL, Base


class RegrasDoBancoTestes(Base):
    def test_defesa_civil_exige_responsavel(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            HistoricoNivel.objects.create(
                area=self.area, nivel_anterior='normal', nivel_novo='alerta', origem=DEFESA_CIVIL
            )

    def test_previsao_nao_define_perigo(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            Previsao.objects.create(
                area=self.area, chuva_mm_24h=90, nivel_calculado=Nivel.PERIGO, fonte='teste'
            )

    def test_chuva_nao_pode_ser_negativa(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            Previsao.objects.create(
                area=self.area, chuva_mm_24h=-1, nivel_calculado=Nivel.NORMAL, fonte='teste'
            )
