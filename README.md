# Motor de Inferencia — Evaluación Crediticia CRM Bancario

Implementación en Python de un motor de inferencia con encadenamiento hacia adelante para la evaluación automatizada de solicitudes de crédito. Desarrollado como Mini Proyecto 2 del curso de Sistemas Basados en Conocimiento en la Universidad CENFOTEC.

---

## ¿Qué hace el sistema?

Recibe el perfil de un solicitante de crédito y produce automáticamente una decisión de aprobación, mostrando la cadena de reglas que llevó a esa conclusión. La evaluación combina cuatro dimensiones:

1. **Perfil RFM del cliente** 
2. **Indicadores financieros** 
3. **Nivel de riesgo** 
4. **Capacidad de pago** 

---

## Requisitos

- Python 3.11 o superior
- No requiere librerías externas

---

## Cómo ejecutarlo

```bash
python mini_proyecto_2.py
```

---

## Salida esperada

```
=== MOTOR DE INFERENCIA CRM BANCARIO ===

=======================================================
  Evaluacion crediticia - CASO-001
=======================================================

--- Datos del solicitante ---
  ID: CASO-001
  Tipo de credito: hipotecario
  Monto solicitado: 60000
  Score crediticio: 820
  Perfil RFM: alto
  ...

--- Indicadores calculados ---
  DTI (deuda/ingreso):    0.0667  (6.7% del ingreso en deudas previas)
  Cuota estimada:         400.0  (monto * 1.2 / plazo)
  Ratio cuota/ingreso:    0.0667  (6.7% del ingreso para la cuota nueva)
  Nivel de riesgo:        bajo
  Capacidad de pago:      holgada

--- Reglas activadas (en orden) ---
  Paso 1: [RN-04] Calculo de ratio deuda/ingreso (DTI)
  Paso 2: [RN-05] Estimacion de cuota mensual del credito
  ...
  Paso 6: [RN-18] Aprobacion directa: riesgo aceptable y capacidad holgada

  Cadena: RN-04 -> RN-05 -> RN-06 -> RN-07 -> RN-11 -> RN-18

--- Decision final ---
  Resultado: [OK] APROBADO
  Regla decisiva: RN-18
  Total reglas activadas: 6
```

---

## Estructura del código

| Sección | Descripción |
|---|---|
| `FRAMES` | Representación declarativa del dominio: 4 frames con slots, tipos y valores posibles |
| `BaseHechos` | Memoria de trabajo del motor: almacena el perfil del cliente y registra la trazabilidad |
| `Regla` + `REGLAS` | 19 reglas de producción SI-ENTONCES organizadas por prioridad |
| `MotorInferencia` | Encadenamiento hacia adelante con condición de punto fijo |
| `TrazaInferencia` | Presentación del razonamiento: entrada, indicadores, cadena de reglas y veredicto |
| `SOLICITUDES` + `ejecutar_motor()` | 5 casos de prueba que cubren todos los caminos de decisión posibles |

---

## Reglas implementadas

| ID | Descripción | Prioridad |
|---|---|---|
| RN-01 | Score no reportado: asume 300 | 100 |
| RN-02 | Deuda no reportada: asume 0 | 100 |
| RN-03 | Garantia no reportada: asume False | 100 |
| RN-04 | Calcula ratio deuda/ingreso (DTI) | 80 |
| RN-05 | Estima cuota mensual del credito | 80 |
| RN-06 | Calcula ratio cuota/ingreso | 80 |
| RN-07 | Score >= 750: riesgo bajo | 60 |
| RN-08 | Score entre 650 y 749: riesgo medio | 60 |
| RN-09 | Score entre 450 y 649: riesgo alto | 60 |
| RN-10 | Score < 450: riesgo critico | 60 |
| RN-11 | Cuota <= 30% del ingreso: capacidad holgada | 50 |
| RN-12 | Cuota entre 30% y 45%: capacidad ajustada | 50 |
| RN-13 | Cuota > 45% del ingreso: capacidad insuficiente | 50 |
| RN-14 | Rechazo: riesgo critico sin garantia | 40 |
| RN-15 | Rechazo: cuota impagable | 35 |
| RN-16 | Aprobacion condicionada: riesgo alto/critico con garantia | 25 |
| RN-17 | Aprobacion condicionada: cliente VIP con capacidad ajustada | 20 |
| RN-18 | Aprobacion directa: riesgo aceptable y capacidad holgada | 10 |
| RN-19 | Rechazo por defecto | 0 |

---

## Casos de prueba incluidos

| Caso | Perfil | Decision esperada | Regla decisiva |
|---|---|---|---|
| CASO-001 | Score 820, ingreso holgado | APROBADO | RN-18 |
| CASO-002 | Score 350, sin garantia | RECHAZADO | RN-14 |
| CASO-003 | Score 430, con garantia | APROBADO_CON_CONDICION | RN-16 |
| CASO-004 | Cuota supera el 45% del ingreso | RECHAZADO | RN-15 |
| CASO-005 | Cliente VIP, capacidad ajustada | APROBADO_CON_CONDICION | RN-17 |

---

## Autores

- Edward Cerdas Rodríguez
- Angelica Saenz Lacayo
- Isabel Galeano Hernandez