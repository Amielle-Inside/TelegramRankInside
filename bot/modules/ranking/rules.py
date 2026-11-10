"""Modulo ranking - regras de pontuacao."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

# Valores de pontuacao (conforme logica.md)
P_TEXTO_PROPRIO = 0.7        # mensagem de texto iniciando participacao
P_REPLY_OUTRA_PESSOA = 1.1   # resposta com texto a mensagem de outra pessoa, fora de sequencia propria
P_SEQ_3_TOTAL = 0.9          # 3 mensagens consecutivas texto sem bonus de resposta (0.7 + 0.1 + 0.1)
P_SEXTA_MESSAGEM_CONSECUTIVA = -0.1  # quarta mensagem nessa sequencia
P_VIDEO_PROPRIO = 0.7        # video com explicacao propria, fora de sequencia
P_LINK_SEM_COMENTARIO = -0.3 # link sem comentario
P_ENCAMINHAMENTO_3_CONSECUTIVOS = -0.6  # 3 encaminhamentos consecutivos (0 - 0.3 - 0.3)

JANALA_MINUTOS = 10          # intervalo para mensagens idênticas repetidas


@dataclass
class MsgMeta:
    """Metadados extraidos de uma mensagem para calculo de pontos."""
    message_id: int
    chat_id: int
    user_id: int
    text: Optional[str]
    is_reply: bool
    reply_to_user_id: Optional[int]
    is_forward: bool
    has_video: bool
    has_link: bool
    caption: Optional[str]
    date_unix: int  # timestamp da mensagem no Telegram


@dataclass
class RuleResult:
    points: float
    reason: str
    applies_bonus: bool = False
    applies_penalty: bool = False


def classify(msg: MsgMeta) -> RuleResult:
    """Aplica regras de pontuacao a uma unica mensagem, considerando contexto."""
    # 1. Mensagem idêntica repetida em <= JANALA_MINUTOS nao gera pontos positivos nem bonus.
    #    Penalidades sao mantidas. (verificado pelo chamador via contexto de janela)

    # 2. Encaminhamento nao pontua positivo; sequencia de 3 encaminhamentos = -0.6 total.
    if msg.is_forward:
        return RuleResult(0.0, "encaminhamento sem pontuacao positiva")

    # 3. Link sem comentario
    if msg.has_link and not msg.text and not msg.caption:
        return RuleResult(P_LINK_SEM_COMENTARIO, "link sem comentario")

    # 4. Vídeo com explicação própria, fora de sequência
    if msg.has_video and msg.text:
        return RuleResult(P_VIDEO_PROPRIO, "video com explicacao propria")

    # 5. Texto próprio (não reply)
    if msg.text and not msg.is_reply:
        return RuleResult(P_TEXTO_PROPRIO, "texto proprio")

    # 6. Resposta a outra pessoa (reply), fora de sequência própria
    if msg.is_reply and msg.reply_to_user_id is not None and msg.reply_to_user_id != msg.user_id:
        return RuleResult(P_REPLY_OUTRA_PESSOA, "resposta a outra pessoa")

    # 7. Texto em sequência própria (reply a si mesmo ou continuação)
    if msg.text:
        return RuleResult(0.1, "complemento de sequencia propria")

    return RuleResult(0.0, "sem pontuacao")


def sequencia_bonus(n_consecutivas: int) -> float:
    """Retorna bonus acumulado para N mensagens consecutivas de texto do mesmo usuario."""
    if n_consecutivas <= 0:
        return 0.0
    if n_consecutivas == 1:
        return P_TEXTO_PROPRIO
    if n_consecutivas == 2:
        return P_TEXTO_PROPRIO + 0.1
    if n_consecutivas == 3:
        return P_SEQ_3_TOTAL  # 0.9
    # 4 ou mais: 0.9 + (n-3) * (-0.1)? Conforme logica: 4a mensagem = -0.1
    # Aqui retornamos o ajuste da mensagem atual (chamador controla)
    return P_SEQ_3_TOTAL + (n_consecutivas - 3) * P_SEXTA_MESSAGEM_CONSECUTIVA
