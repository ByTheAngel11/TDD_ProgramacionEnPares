from decimal import Decimal

from payflow_pago import (
    ESTADO_APROBADA,
    ESTADO_RECHAZADA,
    ESTADO_RECHAZADA_FONDOS,
    procesar_pago_directo,
)


def test_e2e_usuario_realiza_varios_pagos_y_conserva_saldo_correcto():
    saldo = Decimal("10000.00")

    pago_1 = procesar_pago_directo(saldo, 1200, 12, "Misma", "Renta parcial")
    saldo = pago_1.saldo_final

    pago_2 = procesar_pago_directo(saldo, 5001, 12, "Débito", "Proveedor sin token")
    saldo = pago_2.saldo_final

    pago_3 = procesar_pago_directo(saldo, 5001, 12, "Débito", "Proveedor con token", True)
    saldo = pago_3.saldo_final

    pago_4 = procesar_pago_directo(saldo, 5000, 12, "Misma", "Pago mayor al saldo")

    assert pago_1.estado_final == ESTADO_APROBADA
    assert pago_2.estado_final == ESTADO_RECHAZADA
    assert pago_3.estado_final == ESTADO_APROBADA
    assert pago_4.estado_final == ESTADO_RECHAZADA_FONDOS
    assert saldo == Decimal("3799.00")
    assert pago_4.saldo_final == Decimal("3799.00")
