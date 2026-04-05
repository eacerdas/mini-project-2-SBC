# Mini Proyecto 2 - Motor de Inferencia CRM Bancario
# Curso: Inteligencia Artificial / Sistemas Basados en Conocimiento
# Universidad CENFOTEC


# ===========================================================================
# SECCION 1 - REPRESENTACION DEL CONOCIMIENTO
# ===========================================================================

# Frames del dominio: estructuras que representan el conocimiento del sistema.
# Se definieron 4 frames basados en la entrevista con el Director de Marketing.

FRAMES = {

    # Perfil RFM: mide el valor historico del cliente con el banco
    "PerfilRFM": {
        "descripcion": "Valor del cliente segun Recency, Frequency y Monetary.",
        "slots": {
            "valor_rfm": {
                "tipo": "categorico",
                "valores_posibles": ["alto", "medio", "bajo"],
                "descripcion": "Clasificacion general del cliente segun RFM."
            },
            "recency": {
                "tipo": "categorico",
                "valores_posibles": ["muy_reciente", "reciente", "antiguo", "inactivo"],
                "descripcion": "Que tan reciente fue su ultima interaccion con el banco."
            },
            "frequency": {
                "tipo": "categorico",
                "valores_posibles": ["alta", "media", "baja"],
                "descripcion": "Con que frecuencia interactua con el banco."
            },
            "monetary": {
                "tipo": "categorico",
                "valores_posibles": ["alto", "medio", "bajo"],
                "descripcion": "Valor economico que genera el cliente."
            }
        }
    },

    # Solicitud de credito: datos que el cliente entrega al pedir el prestamo
    "SolicitudCredito": {
        "descripcion": "Datos de la solicitud presentada por el cliente.",
        "slots": {
            "tipo_credito": {
                "tipo": "categorico",
                "valores_posibles": ["personal", "hipotecario", "automotriz", "tarjeta", "comercial"],
                "descripcion": "Tipo de producto crediticio solicitado."
            },
            "monto_solicitado": {
                "tipo": "numerico",
                "unidad": "USD",
                "descripcion": "Monto en dolares que pide el cliente."
            },
            "plazo_meses": {
                "tipo": "numerico",
                "unidad": "meses",
                "descripcion": "Plazo de pago en meses."
            },
            "ingreso_mensual": {
                "tipo": "numerico",
                "unidad": "USD",
                "descripcion": "Ingreso mensual declarado."
            },
            "deuda_existente": {
                "tipo": "numerico",
                "unidad": "USD",
                "descripcion": "Deuda mensual preexistente."
            },
            "score_crediticio": {
                "tipo": "numerico",
                "rango": [300, 850],
                "descripcion": "Puntaje del buro de credito."
            },
            "antiguedad_laboral_anos": {
                "tipo": "numerico",
                "unidad": "anos",
                "descripcion": "Anos trabajando en el empleo actual."
            },
            "garantia": {
                "tipo": "booleano",
                "valores_posibles": [True, False],
                "descripcion": "Si el cliente ofrece garantia real o fiador."
            }
        }
    },

    # Indicadores derivados: los calcula el motor, no los da el cliente
    "IndicadoresDerivados": {
        "descripcion": "Ratios calculados por el motor durante la inferencia.",
        "slots": {
            "ratio_deuda_ingreso": {
                "tipo": "numerico",
                "descripcion": "Deuda existente dividida entre ingreso mensual (DTI)."
            },
            "cuota_estimada": {
                "tipo": "numerico",
                "unidad": "USD",
                "descripcion": "Cuota mensual estimada del nuevo credito."
            },
            "ratio_cuota_ingreso": {
                "tipo": "numerico",
                "descripcion": "Cuota estimada dividida entre ingreso mensual."
            },
            "nivel_riesgo": {
                "tipo": "categorico",
                "valores_posibles": ["bajo", "medio", "alto", "critico"],
                "descripcion": "Clasificacion de riesgo segun el score."
            },
            "capacidad_pago": {
                "tipo": "categorico",
                "valores_posibles": ["holgada", "ajustada", "insuficiente"],
                "descripcion": "Si el cliente puede cubrir la cuota mensual."
            }
        }
    },

    # Decision final: resultado que produce el motor
    "DecisionCredito": {
        "descripcion": "Resultado final de la evaluacion crediticia.",
        "slots": {
            "decision": {
                "tipo": "categorico",
                "valores_posibles": ["APROBADO", "APROBADO_CON_CONDICION", "RECHAZADO"],
                "descripcion": "Veredicto del sistema."
            },
            "condicion": {
                "tipo": "texto",
                "descripcion": "Condicion cuando la decision es APROBADO_CON_CONDICION."
            },
            "motivo_rechazo": {
                "tipo": "texto",
                "descripcion": "Razon del rechazo."
            }
        }
    }
}


# Base de Hechos: almacena todo lo que el sistema sabe sobre un cliente.
# Guarda los datos de entrada y los que el motor va calculando.
# Tambien mantiene un registro de lo que fue pasando durante la inferencia.

class BaseHechos:

    def __init__(self, datos_solicitud: dict):
        self._hechos = dict(datos_solicitud)
        self._traza = []
        self._reglas_disparadas = []

    def obtener(self, atributo, default=None):
        return self._hechos.get(atributo, default)

    def establecer(self, atributo, valor, fuente=""):
        valor_anterior = self._hechos.get(atributo)
        self._hechos[atributo] = valor

        if fuente:
            if valor_anterior is None:
                self._traza.append(f"[{fuente}] {atributo} = {valor}")
            else:
                self._traza.append(f"[{fuente}] {atributo}: {valor_anterior} -> {valor}")

    def tiene(self, atributo):
        return atributo in self._hechos and self._hechos[atributo] is not None

    def agregar_nota(self, nota):
        self._traza.append(nota)

    def registrar_regla(self, id_regla):
        self._reglas_disparadas.append(id_regla)

    def todos_los_hechos(self):
        return dict(self._hechos)

    def traza(self):
        return list(self._traza)

    def reglas_disparadas(self):
        return list(self._reglas_disparadas)


# ===========================================================================
# SECCION 2 - REGLAS DE PRODUCCION Y MOTOR DE INFERENCIA
# ===========================================================================

# Cada regla tiene: id, nombre, prioridad, condicion y accion.
# La condicion y la accion son funciones lambda que reciben la base de hechos.

class Regla:

    def __init__(self, id_regla, nombre, prioridad, condicion, accion):
        self.id = id_regla
        self.nombre = nombre
        self.prioridad = prioridad
        self.condicion = condicion
        self.accion = accion

    def es_aplicable(self, base):
        try:
            return self.condicion(base)
        except Exception:
            return False

    def aplicar(self, base):
        base.registrar_regla(self.id)
        self.accion(base)


# Lista de reglas organizadas por bloques segun prioridad.
# Prioridad mas alta = se evalua primero.

REGLAS = [

    # Bloque A - Normalizacion (prioridad 100)
    # Si faltan datos, se asumen valores por defecto para no romper los calculos.

    Regla("RN-01", "Normalizar Score", 100,
          lambda b: not b.tiene("score_crediticio"),
          lambda b: b.establecer("score_crediticio", 300, "RN-01")),

    Regla("RN-02", "Normalizar Deuda", 100,
          lambda b: not b.tiene("deuda_existente"),
          lambda b: b.establecer("deuda_existente", 0.0, "RN-02")),

    Regla("RN-03", "Normalizar Garantia", 100,
          lambda b: not b.tiene("garantia"),
          lambda b: b.establecer("garantia", False, "RN-03")),

    # Bloque B - Indicadores derivados (prioridad 80)
    # Se calculan a partir de los datos de entrada.

    Regla("RN-04", "Calcular DTI", 80,
          lambda b: b.tiene("ingreso_mensual") and b.tiene("deuda_existente")
                    and not b.tiene("ratio_deuda_ingreso"),
          lambda b: b.establecer(
              "ratio_deuda_ingreso",
              round(b.obtener("deuda_existente") / b.obtener("ingreso_mensual"), 4),
              "RN-04")),

    Regla("RN-05", "Estimar Cuota Mensual", 80,
          lambda b: b.tiene("monto_solicitado") and b.tiene("plazo_meses")
                    and not b.tiene("cuota_estimada"),
          lambda b: b.establecer(
              "cuota_estimada",
              round((b.obtener("monto_solicitado") * 1.2) / b.obtener("plazo_meses"), 2),
              "RN-05")),

    Regla("RN-06", "Calcular Ratio Cuota/Ingreso", 80,
          lambda b: b.tiene("cuota_estimada") and b.tiene("ingreso_mensual")
                    and not b.tiene("ratio_cuota_ingreso"),
          lambda b: b.establecer(
              "ratio_cuota_ingreso",
              round(b.obtener("cuota_estimada") / b.obtener("ingreso_mensual"), 4),
              "RN-06")),

    # Bloque C - Nivel de riesgo (prioridad 60)
    # Se clasifica segun el score del buro de credito.

    Regla("RN-07", "Riesgo Bajo", 60,
          lambda b: b.obtener("score_crediticio", 0) >= 750
                    and not b.tiene("nivel_riesgo"),
          lambda b: b.establecer("nivel_riesgo", "bajo", "RN-07")),

    Regla("RN-08", "Riesgo Medio", 60,
          lambda b: 650 <= b.obtener("score_crediticio", 0) < 750
                    and not b.tiene("nivel_riesgo"),
          lambda b: b.establecer("nivel_riesgo", "medio", "RN-08")),

    Regla("RN-09", "Riesgo Alto", 60,
          lambda b: 450 <= b.obtener("score_crediticio", 0) < 650
                    and not b.tiene("nivel_riesgo"),
          lambda b: b.establecer("nivel_riesgo", "alto", "RN-09")),

    Regla("RN-10", "Riesgo Critico", 60,
          lambda b: b.obtener("score_crediticio", 0) < 450
                    and not b.tiene("nivel_riesgo"),
          lambda b: b.establecer("nivel_riesgo", "critico", "RN-10")),

    # Bloque D - Capacidad de pago (prioridad 50)
    # Se evalua que porcentaje del ingreso se iria en la cuota.

    Regla("RN-11", "Capacidad Holgada", 50,
          lambda b: b.obtener("ratio_cuota_ingreso", 1) <= 0.30
                    and not b.tiene("capacidad_pago"),
          lambda b: b.establecer("capacidad_pago", "holgada", "RN-11")),

    Regla("RN-12", "Capacidad Ajustada", 50,
          lambda b: 0.30 < b.obtener("ratio_cuota_ingreso", 1) <= 0.45
                    and not b.tiene("capacidad_pago"),
          lambda b: b.establecer("capacidad_pago", "ajustada", "RN-12")),

    Regla("RN-13", "Capacidad Insuficiente", 50,
          lambda b: b.obtener("ratio_cuota_ingreso", 0) > 0.45
                    and not b.tiene("capacidad_pago"),
          lambda b: b.establecer("capacidad_pago", "insuficiente", "RN-13")),

    # Bloque E - Rechazo directo (prioridad 30-40)

    Regla("RN-14", "Rechazo por Riesgo Critico sin Garantia", 40,
          lambda b: b.obtener("nivel_riesgo") == "critico"
                    and not b.obtener("garantia")
                    and not b.tiene("decision"),
          lambda b: (
              b.establecer("decision", "RECHAZADO", "RN-14"),
              b.establecer("motivo_rechazo",
                           "Riesgo critico sin garantia que lo respalde.", "RN-14")
          )),

    Regla("RN-15", "Rechazo por Cuota Impagable", 35,
          lambda b: b.obtener("capacidad_pago") == "insuficiente"
                    and not b.tiene("decision"),
          lambda b: (
              b.establecer("decision", "RECHAZADO", "RN-15"),
              b.establecer("motivo_rechazo",
                           "La cuota supera el 45% del ingreso mensual.", "RN-15")
          )),

    # Bloque F - Aprobacion con condicion (prioridad 20-25)

    Regla("RN-16", "Aprobacion con Garantia", 25,
          lambda b: b.obtener("nivel_riesgo") in ["alto", "critico"]
                    and b.obtener("garantia")
                    and not b.tiene("decision"),
          lambda b: (
              b.establecer("decision", "APROBADO_CON_CONDICION", "RN-16"),
              b.establecer("condicion",
                           "Aprobado sujeto a formalizacion de la garantia ofrecida.", "RN-16")
          )),

    Regla("RN-17", "Aprobacion Cliente VIP con Capacidad Ajustada", 20,
          lambda b: b.obtener("valor_rfm") == "alto"
                    and b.obtener("capacidad_pago") == "ajustada"
                    and not b.tiene("decision"),
          lambda b: (
              b.establecer("decision", "APROBADO_CON_CONDICION", "RN-17"),
              b.establecer("condicion",
                           "Cliente prioritario: requiere revision manual de ingresos.", "RN-17")
          )),

    # Bloque G - Aprobacion directa (prioridad 10)

    Regla("RN-18", "Aprobacion Directa", 10,
          lambda b: b.obtener("nivel_riesgo") in ["bajo", "medio"]
                    and b.obtener("capacidad_pago") == "holgada"
                    and not b.tiene("decision"),
          lambda b: b.establecer("decision", "APROBADO", "RN-18")),

    # Bloque H - Cierre por defecto (prioridad 0)
    # Si ninguna regla anterior pudo decidir, se rechaza por precaucion.

    Regla("RN-19", "Rechazo por Defecto", 0,
          lambda b: not b.tiene("decision"),
          lambda b: (
              b.establecer("decision", "RECHAZADO", "RN-19"),
              b.establecer("motivo_rechazo",
                           "La solicitud no cumple los criterios minimos de aprobacion.", "RN-19")
          )),
]


# Motor de inferencia: encadenamiento hacia adelante.
# Evalua las reglas ordenadas por prioridad y repite el ciclo
# hasta que ninguna regla nueva se pueda disparar.

class MotorInferencia:

    def __init__(self, lista_reglas):
        self.reglas = sorted(lista_reglas, key=lambda r: r.prioridad, reverse=True)

    def ejecutar(self, base):
        disparadas = set()

        while True:
            hubo_disparo = False
            for regla in self.reglas:
                if regla.id not in disparadas and regla.es_aplicable(base):
                    regla.aplicar(base)
                    disparadas.add(regla.id)
                    hubo_disparo = True
                    break  # reinicia desde la regla de mayor prioridad

            if not hubo_disparo:
                break


# ===========================================================================
# SECCION 3 - TRAZABILIDAD Y PRESENTACION DE RESULTADOS
# ===========================================================================

# Descripciones legibles de cada regla para mostrar en el reporte
DESCRIPCION_REGLAS = {
    "RN-01": "Score no reportado, se asume valor minimo (300)",
    "RN-02": "Deuda no reportada, se asume 0",
    "RN-03": "Garantia no reportada, se asume False",
    "RN-04": "Calculo de ratio deuda/ingreso (DTI)",
    "RN-05": "Estimacion de cuota mensual del credito",
    "RN-06": "Calculo de ratio cuota/ingreso",
    "RN-07": "Score >= 750: riesgo bajo",
    "RN-08": "Score entre 650 y 749: riesgo medio",
    "RN-09": "Score entre 450 y 649: riesgo alto",
    "RN-10": "Score < 450: riesgo critico",
    "RN-11": "Cuota <= 30% del ingreso: capacidad holgada",
    "RN-12": "Cuota entre 30% y 45% del ingreso: capacidad ajustada",
    "RN-13": "Cuota > 45% del ingreso: capacidad insuficiente",
    "RN-14": "Rechazo: riesgo critico sin garantia",
    "RN-15": "Rechazo: cuota supera el 45% del ingreso",
    "RN-16": "Aprobacion condicionada: riesgo alto/critico con garantia",
    "RN-17": "Aprobacion condicionada: cliente VIP con capacidad ajustada",
    "RN-18": "Aprobacion directa: riesgo aceptable y capacidad holgada",
    "RN-19": "Rechazo por defecto: no cumplio ningun criterio de aprobacion",
}


class TrazaInferencia:

    @staticmethod
    def imprimir_hechos_entrada(base):
        print("\n--- Datos del solicitante ---")
        campos = [
            ("ID", "solicitud_id"),
            ("Tipo de credito", "tipo_credito"),
            ("Monto solicitado", "monto_solicitado"),
            ("Plazo (meses)", "plazo_meses"),
            ("Ingreso mensual", "ingreso_mensual"),
            ("Deuda existente", "deuda_existente"),
            ("Score crediticio", "score_crediticio"),
            ("Antiguedad laboral", "antiguedad_laboral_anos"),
            ("Garantia", "garantia"),
            ("Perfil RFM", "valor_rfm"),
        ]
        for etiqueta, atributo in campos:
            print(f"  {etiqueta}: {base.obtener(atributo, 'no reportado')}")

    @staticmethod
    def imprimir_indicadores_derivados(base):
        print("\n--- Indicadores calculados ---")
        dti = base.obtener("ratio_deuda_ingreso", "no calculado")
        cuota = base.obtener("cuota_estimada", "no calculado")
        rci = base.obtener("ratio_cuota_ingreso", "no calculado")
        riesgo = base.obtener("nivel_riesgo", "no calculado")
        capacidad = base.obtener("capacidad_pago", "no calculado")

        print(f"  DTI (deuda/ingreso):    {dti}" +
              (f"  ({dti*100:.1f}% del ingreso en deudas previas)" if isinstance(dti, float) else ""))
        print(f"  Cuota estimada:         {cuota}" +
              ("  (monto * 1.2 / plazo)" if isinstance(cuota, float) else ""))
        print(f"  Ratio cuota/ingreso:    {rci}" +
              (f"  ({rci*100:.1f}% del ingreso para la cuota nueva)" if isinstance(rci, float) else ""))
        print(f"  Nivel de riesgo:        {riesgo}")
        print(f"  Capacidad de pago:      {capacidad}")

    @staticmethod
    def imprimir_cadena_reglas(base):
        print("\n--- Reglas activadas (en orden) ---")
        reglas = base.reglas_disparadas()

        if not reglas:
            print("  Ninguna regla fue disparada.")
            return

        for i, id_regla in enumerate(reglas, start=1):
            descripcion = DESCRIPCION_REGLAS.get(id_regla, "sin descripcion")
            print(f"  Paso {i}: [{id_regla}] {descripcion}")

        print(f"\n  Cadena: {' -> '.join(reglas)}")

    @staticmethod
    def imprimir_decision(base):
        print("\n--- Decision final ---")
        decision = base.obtener("decision", "SIN DECISION")

        simbolo = {"APROBADO": "[OK]", "APROBADO_CON_CONDICION": "[COND]", "RECHAZADO": "[X]"}
        print(f"  Resultado: {simbolo.get(decision, '?')} {decision}")

        if base.tiene("motivo_rechazo"):
            print(f"  Motivo:    {base.obtener('motivo_rechazo')}")
        if base.tiene("condicion"):
            print(f"  Condicion: {base.obtener('condicion')}")

        reglas = base.reglas_disparadas()
        print(f"  Regla decisiva: {reglas[-1] if reglas else 'ninguna'}")
        print(f"  Total reglas activadas: {len(reglas)}")

    @staticmethod
    def reporte_completo(base):
        caso_id = base.obtener("solicitud_id", "sin ID")
        print("\n" + "=" * 55)
        print(f"  Evaluacion crediticia - {caso_id}")
        print("=" * 55)
        TrazaInferencia.imprimir_hechos_entrada(base)
        TrazaInferencia.imprimir_indicadores_derivados(base)
        TrazaInferencia.imprimir_cadena_reglas(base)
        TrazaInferencia.imprimir_decision(base)
        print("=" * 55)


# Casos de prueba: cubren los 5 caminos posibles del motor

SOLICITUDES = [

    # Caso 1: perfil ideal, se espera APROBADO
    {
        "solicitud_id": "CASO-001",
        "tipo_credito": "hipotecario",
        "monto_solicitado": 60000,
        "plazo_meses": 180,
        "ingreso_mensual": 6000,
        "deuda_existente": 400,
        "score_crediticio": 820,
        "antiguedad_laboral_anos": 8,
        "garantia": False,
        "valor_rfm": "alto",
        "recency": "muy_reciente",
        "frequency": "alta",
        "monetary": "alto",
    },

    # Caso 2: score critico sin garantia, se espera RECHAZADO
    {
        "solicitud_id": "CASO-002",
        "tipo_credito": "personal",
        "monto_solicitado": 3000,
        "plazo_meses": 12,
        "ingreso_mensual": 1200,
        "deuda_existente": 100,
        "score_crediticio": 350,
        "antiguedad_laboral_anos": 1,
        "garantia": False,
        "valor_rfm": "bajo",
        "recency": "inactivo",
        "frequency": "baja",
        "monetary": "bajo",
    },

    # Caso 3: score critico pero tiene garantia, se espera APROBADO_CON_CONDICION
    {
        "solicitud_id": "CASO-003",
        "tipo_credito": "automotriz",
        "monto_solicitado": 15000,
        "plazo_meses": 48,
        "ingreso_mensual": 2000,
        "deuda_existente": 100,
        "score_crediticio": 430,
        "antiguedad_laboral_anos": 2,
        "garantia": True,
        "valor_rfm": "medio",
        "recency": "reciente",
        "frequency": "media",
        "monetary": "medio",
    },

    # Caso 4: cuota supera el 45% del ingreso, se espera RECHAZADO
    {
        "solicitud_id": "CASO-004",
        "tipo_credito": "personal",
        "monto_solicitado": 20000,
        "plazo_meses": 24,
        "ingreso_mensual": 1800,
        "deuda_existente": 0,
        "score_crediticio": 720,
        "antiguedad_laboral_anos": 3,
        "garantia": False,
        "valor_rfm": "bajo",
        "recency": "antiguo",
        "frequency": "baja",
        "monetary": "bajo",
    },

    # Caso 5: cliente VIP con capacidad ajustada, se espera APROBADO_CON_CONDICION
    # cuota = (40000 * 1.2) / 60 = 800, ratio = 800/2200 = 36.4%
    {
        "solicitud_id": "CASO-005",
        "tipo_credito": "comercial",
        "monto_solicitado": 40000,
        "plazo_meses": 60,
        "ingreso_mensual": 2200,
        "deuda_existente": 200,
        "score_crediticio": 680,
        "antiguedad_laboral_anos": 6,
        "garantia": False,
        "valor_rfm": "alto",
        "recency": "muy_reciente",
        "frequency": "alta",
        "monetary": "alto",
    },
]


def ejecutar_motor():
    motor = MotorInferencia(REGLAS)
    resumen = []

    print("\n=== MOTOR DE INFERENCIA CRM BANCARIO ===")

    for perfil in SOLICITUDES:
        base = BaseHechos(perfil)
        motor.ejecutar(base)
        TrazaInferencia.reporte_completo(base)

        resumen.append({
            "id": base.obtener("solicitud_id"),
            "decision": base.obtener("decision"),
            "reglas": " -> ".join(base.reglas_disparadas()),
        })

    print("\n=== RESUMEN GENERAL ===")
    print(f"\n  {'CASO':<12} {'DECISION':<28} REGLAS ACTIVADAS")
    print("  " + "-" * 80)
    for fila in resumen:
        print(f"  {fila['id']:<12} {fila['decision']:<28} {fila['reglas']}")
    print()


if __name__ == "__main__":
    ejecutar_motor()