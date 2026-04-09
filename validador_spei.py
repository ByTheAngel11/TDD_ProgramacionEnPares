from __future__ import annotations

from dataclasses import dataclass

ESTADO_PENDIENTE = "PENDIENTE"
ESTADO_APROBADA = "APROBADA"
ESTADO_RECHAZADA = "RECHAZADA_POR_POLITICA"

TIPO_MISMA = "Misma"
TIPO_DEBITO = "Débito"
TIPO_CREDITO = "Crédito"


@dataclass(frozen=True)
class ResultadoTransferencia:
    estado_inicial: str
    estado_final: str
    procedente: bool


class ErrorValidacionTransferencia(ValueError):
    """Se lanza cuando los datos de entrada no son válidos."""


def _normalizar_tipo_cuenta(tipo_cuenta_destino: str) -> str:
    if not isinstance(tipo_cuenta_destino, str):
        raise ErrorValidacionTransferencia("tipo_cuenta_destino debe ser una cadena")

    tipo = tipo_cuenta_destino.strip().lower()
    equivalencias = {
        "misma": TIPO_MISMA,
        "debito": TIPO_DEBITO,
        "débito": TIPO_DEBITO,
        "credito": TIPO_CREDITO,
        "crédito": TIPO_CREDITO,
    }

    if tipo not in equivalencias:
        raise ErrorValidacionTransferencia(
            'tipo_cuenta_destino debe ser "Misma", "Débito" o "Crédito"'
        )

    return equivalencias[tipo]


def _validar_entrada(monto: float, hora_transferencia: int) -> None:
    if not isinstance(monto, (int, float)):
        raise ErrorValidacionTransferencia("monto debe ser numérico")
    if monto < 0:
        raise ErrorValidacionTransferencia("monto no puede ser negativo")
    if not isinstance(hora_transferencia, int):
        raise ErrorValidacionTransferencia("hora_transferencia debe ser un entero")
    if not 0 <= hora_transferencia <= 23:
        raise ErrorValidacionTransferencia("hora_transferencia debe estar entre 0 y 23")


def validar_transferencia(
    monto: float,
    hora_transferencia: int,
    tipo_cuenta_destino: str,
    token_activo: bool = False,
) -> ResultadoTransferencia:
    """
    Evalúa si una transferencia es aprobada o rechazada según las políticas.

    Reglas:
    - Misma: siempre aprobada.
    - Crédito: solo entre 09:00 y 18:00, inclusive.
    - Débito: hasta 5000 sin token; arriba de 5000 requiere token_activo=True.

    Regresa un ResultadoTransferencia con estado inicial y final.
    """
    _validar_entrada(monto, hora_transferencia)
    tipo_normalizado = _normalizar_tipo_cuenta(tipo_cuenta_destino)

    estado_inicial = ESTADO_PENDIENTE

    if tipo_normalizado == TIPO_MISMA:
        return ResultadoTransferencia(estado_inicial, ESTADO_APROBADA, True)

    if tipo_normalizado == TIPO_CREDITO:
        aprobada = 9 <= hora_transferencia <= 18
        return ResultadoTransferencia(
            estado_inicial,
            ESTADO_APROBADA if aprobada else ESTADO_RECHAZADA,
            aprobada,
        )

    # tipo == Débito
    aprobada = monto <= 5000 or token_activo
    return ResultadoTransferencia(
        estado_inicial,
        ESTADO_APROBADA if aprobada else ESTADO_RECHAZADA,
        aprobada,
    )