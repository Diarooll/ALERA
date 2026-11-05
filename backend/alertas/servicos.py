from django.db import transaction
from django.utils import timezone

from locais.models import AreaRisco

from .models import HistoricoNivel


@transaction.atomic
def mudar_nivel(area, nivel, origem, responsavel=None):
    """Muda o nível da área e grava o histórico juntos. Sem mudança, não grava nada."""
    area = AreaRisco.objects.select_for_update().get(pk=area.pk)
    if area.nivel == nivel:
        return None

    historico = HistoricoNivel.objects.create(
        area=area,
        nivel_anterior=area.nivel,
        nivel_novo=nivel,
        origem=origem,
        responsavel=responsavel,
    )
    area.nivel = nivel
    area.nivel_atualizado_em = timezone.now()
    area.save(update_fields=['nivel', 'nivel_atualizado_em'])
    return historico
