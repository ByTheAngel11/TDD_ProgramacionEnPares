from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP

ESTADO_PENDIENTE = "PENDIENTE"
ESTADO_APROBADA = "APROBADA"
ESTADO_RECHAZADA = "RECHAZADA_POR_POLITICA"
ESTADO_RECHAZADA_FONDOS = "RECHAZADA_FONDOS_INSUFICIENTES"

TIPO_MISMA = "Misma"
TIPO_DEBITO = "Débito"
TIPO_CREDITO = "Crédito"

MOTIVO_APROBADA = "Transferencia aprobada"
MOTIVO_POLITICA = "Transferencia rechazada por política SPEI"
MOTIVO_FONDOS = "Saldo insuficiente para completar el pago"


class ErrorValidacionTransferencia(ValueError):
    """Se lanza cuando los datos de entrada no son válidos."""


@dataclass(frozen=True)
class ResultadoTransferencia:
    estado_inicial: str
    estado_final: str
    procedente: bool


@dataclass(frozen=True)
class PagoProcesado:
    estado_inicial: str
    estado_final: str
    procedente: bool
    monto: Decimal
    saldo_inicial: Decimal
    saldo_final: Decimal
    concepto: str
    tipo_cuenta_destino: str
    motivo: str


def _a_decimal(valor: int | float | str | Decimal, nombre: str) -> Decimal:
    if isinstance(valor, bool):
        raise ErrorValidacionTransferencia(f"{nombre} debe ser numérico")
    try:
        decimal = Decimal(str(valor))
    except Exception as exc:  # pragma: no cover - protección defensiva
        raise ErrorValidacionTransferencia(f"{nombre} debe ser numérico") from exc
    return decimal.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _normalizar_tipo_cuenta(tipo_cuenta_destino: str) -> str:
    if not isinstance(tipo_cuenta_destino, str):
        raise ErrorValidacionTransferencia("tipo_cuenta_destino debe ser una cadena")

    equivalencias = {
        "misma": TIPO_MISMA,
        "debito": TIPO_DEBITO,
        "débito": TIPO_DEBITO,
        "credito": TIPO_CREDITO,
        "crédito": TIPO_CREDITO,
    }
    tipo = tipo_cuenta_destino.strip().lower()

    if tipo not in equivalencias:
        raise ErrorValidacionTransferencia(
            'tipo_cuenta_destino debe ser "Misma", "Débito" o "Crédito"'
        )

    return equivalencias[tipo]


def validar_concepto(concepto: str) -> str:
    if not isinstance(concepto, str):
        raise ErrorValidacionTransferencia("concepto debe ser una cadena")

    concepto_limpio = concepto.strip()
    if not concepto_limpio:
        raise ErrorValidacionTransferencia("concepto no puede estar vacío")

    if len(concepto_limpio) > 60:
        raise ErrorValidacionTransferencia("concepto no puede exceder 60 caracteres")

    return concepto_limpio


def _validar_hora(hora_transferencia: int) -> None:
    if not isinstance(hora_transferencia, int) or isinstance(hora_transferencia, bool):
        raise ErrorValidacionTransferencia("hora_transferencia debe ser un entero")

    if not 0 <= hora_transferencia <= 23:
        raise ErrorValidacionTransferencia("hora_transferencia debe estar entre 0 y 23")


def _validar_monto_transferencia(monto: int | float | str | Decimal) -> Decimal:
    monto_decimal = _a_decimal(monto, "monto")
    if monto_decimal < 0:
        raise ErrorValidacionTransferencia("monto no puede ser negativo")
    return monto_decimal


def _validar_monto_pago(monto: int | float | str | Decimal) -> Decimal:
    monto_decimal = _validar_monto_transferencia(monto)
    if monto_decimal <= 0:
        raise ErrorValidacionTransferencia("monto debe ser mayor a cero")
    return monto_decimal


def validar_transferencia(
    monto: int | float | str | Decimal,
    hora_transferencia: int,
    tipo_cuenta_destino: str,
    token_activo: bool = False,
) -> ResultadoTransferencia:
    """Evalúa si una transferencia SPEI procede según la política mínima del MPV."""
    monto_decimal = _validar_monto_transferencia(monto)
    _validar_hora(hora_transferencia)
    tipo_normalizado = _normalizar_tipo_cuenta(tipo_cuenta_destino)

    if tipo_normalizado == TIPO_MISMA:
        return _resultado_aprobado()

    if tipo_normalizado == TIPO_CREDITO:
        return _resultado_por_politica(9 <= hora_transferencia <= 18)

    return _resultado_por_politica(monto_decimal <= Decimal("5000.00") or token_activo)


def calcular_saldo_final(saldo_actual: int | float | str | Decimal, monto: int | float | str | Decimal) -> Decimal:
    saldo_decimal = _a_decimal(saldo_actual, "saldo_actual")
    monto_decimal = _validar_monto_pago(monto)

    if saldo_decimal < 0:
        raise ErrorValidacionTransferencia("saldo_actual no puede ser negativo")

    return (saldo_decimal - monto_decimal).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def procesar_pago_directo(
    saldo_actual: int | float | str | Decimal,
    monto: int | float | str | Decimal,
    hora_transferencia: int,
    tipo_cuenta_destino: str,
    concepto: str,
    token_activo: bool = False,
) -> PagoProcesado:
    """Orquesta el flujo MPV: validar datos, aplicar política SPEI y actualizar saldo."""
    saldo_decimal = _a_decimal(saldo_actual, "saldo_actual")
    if saldo_decimal < 0:
        raise ErrorValidacionTransferencia("saldo_actual no puede ser negativo")

    monto_decimal = _validar_monto_pago(monto)
    concepto_limpio = validar_concepto(concepto)
    transferencia = validar_transferencia(monto_decimal, hora_transferencia, tipo_cuenta_destino, token_activo)
    tipo_normalizado = _normalizar_tipo_cuenta(tipo_cuenta_destino)

    if not transferencia.procedente:
        return _pago_rechazado(
            saldo_decimal,
            monto_decimal,
            concepto_limpio,
            tipo_normalizado,
            ESTADO_RECHAZADA,
            MOTIVO_POLITICA,
        )

    if saldo_decimal < monto_decimal:
        return _pago_rechazado(
            saldo_decimal,
            monto_decimal,
            concepto_limpio,
            tipo_normalizado,
            ESTADO_RECHAZADA_FONDOS,
            MOTIVO_FONDOS,
        )

    return PagoProcesado(
        estado_inicial=ESTADO_PENDIENTE,
        estado_final=ESTADO_APROBADA,
        procedente=True,
        monto=monto_decimal,
        saldo_inicial=saldo_decimal,
        saldo_final=calcular_saldo_final(saldo_decimal, monto_decimal),
        concepto=concepto_limpio,
        tipo_cuenta_destino=tipo_normalizado,
        motivo=MOTIVO_APROBADA,
    )


def _resultado_aprobado() -> ResultadoTransferencia:
    return ResultadoTransferencia(ESTADO_PENDIENTE, ESTADO_APROBADA, True)


def _resultado_por_politica(aprobada: bool) -> ResultadoTransferencia:
    estado_final = ESTADO_APROBADA if aprobada else ESTADO_RECHAZADA
    return ResultadoTransferencia(ESTADO_PENDIENTE, estado_final, aprobada)


def _pago_rechazado(
    saldo_actual: Decimal,
    monto: Decimal,
    concepto: str,
    tipo_cuenta_destino: str,
    estado_final: str,
    motivo: str,
) -> PagoProcesado:
    return PagoProcesado(
        estado_inicial=ESTADO_PENDIENTE,
        estado_final=estado_final,
        procedente=False,
        monto=monto,
        saldo_inicial=saldo_actual,
        saldo_final=saldo_actual,
        concepto=concepto,
        tipo_cuenta_destino=tipo_cuenta_destino,
        motivo=motivo,
    )
