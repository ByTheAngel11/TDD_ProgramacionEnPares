# TAR04 - PayFlow TDD

Repositorio base usado: https://github.com/ByTheAngel11/TDD_ProgramacionEnPares

## Archivos principales

- `payflow_pago.py`: código productivo del MPV, con validación SPEI, validación de concepto, cálculo de saldo y orquestadora `procesar_pago_directo`.
- `validador_spei.py`: archivo de compatibilidad con la línea base original.
- `tests/test_validador_spei.py`: pruebas unitarias.
- `tests/test_payflow_pago_directo.py`: pruebas de integración interna.
- `tests/test_e2e_payflow.py`: prueba E2E adicional.
- `evidencias/coverage.txt`: salida de cobertura.
- `evidencias/radon_cc.txt`: salida de complejidad ciclomática.

## Comandos

```bash
pip install -r requirements.txt
pytest --cov=payflow_pago --cov-report=term-missing
radon cc payflow_pago.py -s
```

## Resultado final validado

- 52 pruebas aprobadas.
- 100% de cobertura sobre `payflow_pago.py`.
- Todos los bloques en complejidad A con Radon.
