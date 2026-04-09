import pytest

from validador_spei import (
    ESTADO_APROBADA,
    ESTADO_PENDIENTE,
    ESTADO_RECHAZADA,
    ErrorValidacionTransferencia,
    validar_transferencia,
)


@pytest.mark.parametrize(
    "monto,hora,tipo,token,estado_esperado,procedente_esperado",
    [
        # Misma cuenta: siempre procede
        (1000, 2, "Misma", False, ESTADO_APROBADA, True),
        (25000, 23, "Misma", False, ESTADO_APROBADA, True),
        # Crédito: horario permitido
        (1000, 9, "Crédito", False, ESTADO_APROBADA, True),
        (1000, 18, "Crédito", False, ESTADO_APROBADA, True),
        # Crédito: fuera de horario
        (1000, 8, "Crédito", False, ESTADO_RECHAZADA, False),
        (1000, 19, "Crédito", False, ESTADO_RECHAZADA, False),
        # Débito: hasta 5000 sin token
        (5000, 10, "Débito", False, ESTADO_APROBADA, True),
        (3500, 22, "Débito", False, ESTADO_APROBADA, True),
        # Débito: mayor a 5000 sin token
        (5001, 10, "Débito", False, ESTADO_RECHAZADA, False),
        (9000, 14, "Débito", False, ESTADO_RECHAZADA, False),
        # Débito: mayor a 5000 con token
        (5001, 10, "Débito", True, ESTADO_APROBADA, True),
        (12000, 6, "Débito", True, ESTADO_APROBADA, True),
    ],
)
def test_validar_transferencia_parametrizada(
    monto,
    hora,
    tipo,
    token,
    estado_esperado,
    procedente_esperado,
):
    resultado = validar_transferencia(monto, hora, tipo, token)

    assert resultado.estado_inicial == ESTADO_PENDIENTE
    assert resultado.estado_final == estado_esperado
    assert resultado.procedente is procedente_esperado


@pytest.mark.parametrize(
    "monto,hora,tipo,token",
    [
        (-1, 10, "Débito", False),
        (1000, -1, "Débito", False),
        (1000, 24, "Débito", False),
        (1000, 10, "Ahorro", False),
    ],
)
def test_entradas_invalidas_lanzan_error(monto, hora, tipo, token):
    with pytest.raises(ErrorValidacionTransferencia):
        validar_transferencia(monto, hora, tipo, token)