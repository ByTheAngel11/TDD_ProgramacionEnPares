from decimal import Decimal

import pytest

from payflow_pago import (
    ESTADO_APROBADA,
    ESTADO_PENDIENTE,
    ESTADO_RECHAZADA,
    ESTADO_RECHAZADA_FONDOS,
    ErrorValidacionTransferencia,
    MOTIVO_APROBADA,
    MOTIVO_FONDOS,
    MOTIVO_POLITICA,
    TIPO_CREDITO,
    TIPO_DEBITO,
    TIPO_MISMA,
    procesar_pago_directo,
)


@pytest.mark.parametrize(
    "saldo,monto,hora,tipo,token,saldo_esperado,tipo_esperado",
    [
        (1000, 250, 7, "Misma", False, Decimal("750.00"), TIPO_MISMA),
        (7000, 5000, 23, "Débito", False, Decimal("2000.00"), TIPO_DEBITO),
        (9000, 5001, 22, "Débito", True, Decimal("3999.00"), TIPO_DEBITO),
        (2500, 1000, 9, "credito", False, Decimal("1500.00"), TIPO_CREDITO),
        (2500, 1000, 18, "Crédito", False, Decimal("1500.00"), TIPO_CREDITO),
    ],
)
def test_procesar_pago_directo_aprueba_flujos_validos(
    saldo, monto, hora, tipo, token, saldo_esperado, tipo_esperado
):
    resultado = procesar_pago_directo(
        saldo_actual=saldo,
        monto=monto,
        hora_transferencia=hora,
        tipo_cuenta_destino=tipo,
        concepto="Pago proveedor",
        token_activo=token,
    )

    assert resultado.estado_inicial == ESTADO_PENDIENTE
    assert resultado.estado_final == ESTADO_APROBADA
    assert resultado.procedente is True
    assert resultado.saldo_final == saldo_esperado
    assert resultado.concepto == "Pago proveedor"
    assert resultado.tipo_cuenta_destino == tipo_esperado
    assert resultado.motivo == MOTIVO_APROBADA


@pytest.mark.parametrize(
    "saldo,monto,hora,tipo,token",
    [
        (8000, 5001, 12, "Débito", False),
        (8000, 1000, 8, "Crédito", False),
        (8000, 1000, 19, "Crédito", False),
    ],
)
def test_procesar_pago_directo_rechaza_por_politica_sin_tocar_saldo(
    saldo, monto, hora, tipo, token
):
    resultado = procesar_pago_directo(
        saldo_actual=saldo,
        monto=monto,
        hora_transferencia=hora,
        tipo_cuenta_destino=tipo,
        concepto="Pago validado",
        token_activo=token,
    )

    assert resultado.estado_final == ESTADO_RECHAZADA
    assert resultado.procedente is False
    assert resultado.saldo_inicial == Decimal(str(saldo)).quantize(Decimal("0.01"))
    assert resultado.saldo_final == resultado.saldo_inicial
    assert resultado.motivo == MOTIVO_POLITICA


def test_procesar_pago_directo_rechaza_por_fondos_sin_tocar_saldo():
    resultado = procesar_pago_directo(
        saldo_actual=1000,
        monto=1500,
        hora_transferencia=10,
        tipo_cuenta_destino="Misma",
        concepto="Pago de servicio",
    )

    assert resultado.estado_final == ESTADO_RECHAZADA_FONDOS
    assert resultado.procedente is False
    assert resultado.saldo_inicial == Decimal("1000.00")
    assert resultado.saldo_final == Decimal("1000.00")
    assert resultado.motivo == MOTIVO_FONDOS


@pytest.mark.parametrize(
    "saldo,monto,hora,tipo,concepto",
    [
        (-1, 100, 12, "Misma", "Pago"),
        (1000, 0, 12, "Misma", "Pago"),
        (1000, 100, 24, "Misma", "Pago"),
        (1000, 100, 12, "Ahorro", "Pago"),
        (1000, 100, 12, "Misma", ""),
    ],
)
def test_procesar_pago_directo_entradas_invalidas(saldo, monto, hora, tipo, concepto):
    with pytest.raises(ErrorValidacionTransferencia):
        procesar_pago_directo(saldo, monto, hora, tipo, concepto)
