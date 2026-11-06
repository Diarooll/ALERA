from django.db import transaction
from django.utils import timezone

from locais.models import AreaRisco

from .models import HistoricoNivel


@transaction.atomic
def mudar_nivel(area, nivel, origem, responsavel=None, mensagem=None):
    """Muda o nível da área e grava o histórico juntos.

    A mensagem (orientação da Defesa Civil) fica na área para o app do morador.
    Quem não manda mensagem (a previsão) só grava quando o nível muda, e aí a orientação
    antiga sai: o app volta a usar o texto padrão do nível.
    """
    area = AreaRisco.objects.select_for_update().get(pk=area.pk)
    mensagem = (mensagem or '').strip() if mensagem is not None else None
    if area.nivel == nivel and (mensagem is None or area.orientacao == mensagem):
        return None
    mensagem = mensagem or ''

    historico = HistoricoNivel.objects.create(
        area=area,
        nivel_anterior=area.nivel,
        nivel_novo=nivel,
        origem=origem,
        responsavel=responsavel,
        mensagem=mensagem,
    )
    area.nivel = nivel
    area.orientacao = mensagem
    area.nivel_atualizado_em = timezone.now()
    area.save(update_fields=['nivel', 'orientacao', 'nivel_atualizado_em'])
    return historico
