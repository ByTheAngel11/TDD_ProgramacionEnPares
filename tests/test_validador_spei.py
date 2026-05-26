from decimal import Decimal

import pytest

from payflow_pago import (
    ESTADO_APROBADA,
    ESTADO_PENDIENTE,
    ESTADO_RECHAZADA,
    ErrorValidacionTransferencia,
    TIPO_CREDITO,
    TIPO_DEBITO,
    TIPO_MISMA,
    calcular_saldo_final,
    validar_concepto,
    validar_transferencia,
)


@pytest.mark.parametrize(
    "monto,hora,tipo,token,estado_esperado,procedente_esperado",
    [
        (1000, 2, "Misma", False, ESTADO_APROBADA, True),
        (25000, 23, "Misma", False, ESTADO_APROBADA, True),
        (1000, 9, "Crédito", False, ESTADO_APROBADA, True),
        (1000, 18, "Crédito", False, ESTADO_APROBADA, True),
        (1000, 8, "Crédito", False, ESTADO_RECHAZADA, False),
        (1000, 19, "Crédito", False, ESTADO_RECHAZADA, False),
        (5000, 10, "Débito", False, ESTADO_APROBADA, True),
        (3500, 22, "Débito", False, ESTADO_APROBADA, True),
        (5001, 10, "Débito", False, ESTADO_RECHAZADA, False),
        (9000, 14, "Débito", False, ESTADO_RECHAZADA, False),
        (5001, 10, "Débito", True, ESTADO_APROBADA, True),
        (12000, 6, "Débito", True, ESTADO_APROBADA, True),
    ],
)
def test_validar_transferencia_parametrizada(
    monto, hora, tipo, token, estado_esperado, procedente_esperado
):
    resultado = validar_transferencia(monto, hora, tipo, token)

    assert resultado.estado_inicial == ESTADO_PENDIENTE
    assert resultado.estado_final == estado_esperado
    assert resultado.procedente is procedente_esperado


@pytest.mark.parametrize(
    "tipo_entrada,tipo_esperado",
    [
        (" misma ", TIPO_MISMA),
        ("debito", TIPO_DEBITO),
        ("DÉBITO", TIPO_DEBITO),
        ("credito", TIPO_CREDITO),
        ("Crédito", TIPO_CREDITO),
    ],
)
def test_normaliza_tipos_de_cuenta_validos(tipo_entrada, tipo_esperado):
    resultado = validar_transferencia(100, 12, tipo_entrada)

    assert resultado.estado_inicial == ESTADO_PENDIENTE
    assert resultado.estado_final == ESTADO_APROBADA
    assert resultado.procedente is True


@pytest.mark.parametrize(
    "monto,hora,tipo,token",
    [
        (-1, 10, "Débito", False),
        (1000, -1, "Débito", False),
        (1000, 24, "Débito", False),
        (1000, 10, "Ahorro", False),
        (1000, 10, None, False),
        (1000, 10.5, "Débito", False),
        (1000, True, "Débito", False),
        (True, 10, "Débito", False),
        ("abc", 10, "Débito", False),
    ],
)
def test_entradas_invalidas_lanzan_error(monto, hora, tipo, token):
    with pytest.raises(ErrorValidacionTransferencia):
        validar_transferencia(monto, hora, tipo, token)


@pytest.mark.parametrize("concepto", ["Renta mayo", "  Pago escuela  "])
def test_validar_concepto_limpia_texto_valido(concepto):
    assert validar_concepto(concepto) == concepto.strip()


@pytest.mark.parametrize("concepto", ["", "   ", None, "x" * 61])
def test_validar_concepto_rechaza_texto_invalido(concepto):
    with pytest.raises(ErrorValidacionTransferencia):
        validar_concepto(concepto)


def test_calcular_saldo_final_descuenta_monto_y_redondea():
    assert calcular_saldo_final("1000.005", "100.004") == Decimal("900.01")


@pytest.mark.parametrize("saldo,monto", [(-1, 100), (100, 0), (100, -5), (True, 5)])
def test_calcular_saldo_final_valida_datos(saldo, monto):
    with pytest.raises(ErrorValidacionTransferencia):
        calcular_saldo_final(saldo, monto)
