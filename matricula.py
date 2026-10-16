import os
import csv
from datetime import datetime

# --- Configuracion ----------------------------------------------------------

CARPETA_DATOS = "datos"
RUTA_SOLICITUDES = os.path.join(CARPETA_DATOS, "solicitudes.csv")
RUTA_VACANTES = os.path.join(CARPETA_DATOS, "vacantes.csv")

CAMPOS_SOLICITUD = [
    "dni",
    "nombre",
    "apellido",
    "fecha_nacimiento",
    "grado",
    "colegio_procedencia",
    "doc_dni",
    "doc_partida_nacimiento",
    "doc_comprobante_pago",
    "estado",
]

ESTADOS = (
    "pendiente",
    "observada",
    "lista_espera",
    "aprobada",
    "pagada",
    "lista_constancia",
    "matriculado",
)


# --- Persistencia -----------------------------------------------------------

def cargar_solicitudes():
    if not os.path.exists(RUTA_SOLICITUDES):
        return []

    with open(RUTA_SOLICITUDES, newline="", encoding="utf-8") as archivo:
        return list(csv.DictReader(archivo))


def guardar_solicitudes(solicitudes):
    os.makedirs(CARPETA_DATOS, exist_ok=True)

    with open(RUTA_SOLICITUDES, "w", newline="", encoding="utf-8") as archivo:
        escritor = csv.DictWriter(
            archivo,
            fieldnames=CAMPOS_SOLICITUD
        )
        escritor.writeheader()
        escritor.writerows(solicitudes)


def cargar_vacantes():
    """Devuelve {grado: {"totales": int, "disponibles": int}}."""
    if not os.path.exists(RUTA_VACANTES):
        return {}

    with open(RUTA_VACANTES, newline="", encoding="utf-8") as archivo:
        vacantes = {}

        for fila in csv.DictReader(archivo):
            disponibles = int(fila["cupos_disponibles"])
            totales = int(fila.get("cupos_totales") or disponibles)

            vacantes[fila["grado"]] = {
                "totales": totales,
                "disponibles": disponibles,
            }

        return vacantes


def guardar_vacantes(vacantes):
    os.makedirs(CARPETA_DATOS, exist_ok=True)

    with open(RUTA_VACANTES, "w", newline="", encoding="utf-8") as archivo:
        escritor = csv.writer(archivo)
        escritor.writerow(["grado", "cupos_totales", "cupos_disponibles"])

        for grado, cupos in vacantes.items():
            escritor.writerow([grado, cupos["totales"], cupos["disponibles"]])


# --- Reglas de negocio ------------------------------------------------------

def documentos_completos(solicitud):
    requiere_comprobante = solicitud["estado"] in (
        "pagada",
        "lista_constancia",
        "matriculado",
    )

    tiene_comprobante = (
        solicitud["doc_comprobante_pago"] == "si"
        or not requiere_comprobante
    )

    return (
        solicitud["doc_dni"] == "si"
        and solicitud["doc_partida_nacimiento"] == "si"
        and tiene_comprobante
    )


def hay_vacante(vacantes, grado):
    return vacantes.get(grado, {}).get("disponibles", 0) > 0


def validar_solicitudes_pendientes(solicitudes, vacantes):
    """Procesa 'pendiente' y 'lista_espera' en orden de registro.

    - Documentos incompletos -> observada.
    - Documentos completos sin vacante -> lista_espera.
    - Documentos completos con vacante -> aprobada (descuenta un cupo).
    """
    resultado = {
        "aprobadas": 0,
        "observadas": 0,
        "en_espera": 0,
    }

    for solicitud in solicitudes:
        if solicitud["estado"] not in ("pendiente", "lista_espera"):
            continue

        grado = solicitud["grado"]

        if not documentos_completos(solicitud):
            solicitud["estado"] = "observada"
            resultado["observadas"] += 1

        elif hay_vacante(vacantes, grado):
            solicitud["estado"] = "aprobada"
            vacantes[grado]["disponibles"] -= 1
            resultado["aprobadas"] += 1

        else:
            solicitud["estado"] = "lista_espera"
            resultado["en_espera"] += 1

    return resultado


# --- Operaciones de la secretaria ------------------------------------------

def registrar_solicitud(solicitudes, vacantes):
    print("\n-- Registrar solicitud de matricula --")

    if not vacantes:
        print(
            "No hay grados configurados. "
            "Revisa el archivo datos/vacantes.csv."
        )
        return

    dni = input("DNI del estudiante: ").strip()

    if not dni.isdigit() or len(dni) != 8:
        print("Error: el DNI debe tener 8 digitos.")
        return

    if _buscar_por_dni(solicitudes, dni) is not None:
        print("Ya existe una solicitud con ese DNI.")
        return

    solicitud = {
        "dni": dni,
        "nombre": input("Nombre: ").strip(),
        "apellido": input("Apellido: ").strip(),
        "fecha_nacimiento": input(
            "Fecha de nacimiento (DD/MM/AAAA): "
        ).strip(),
        "grado": _pedir_grado(vacantes),
        "colegio_procedencia": input(
            "Colegio de procedencia: "
        ).strip(),
        "doc_dni": "no",
        "doc_partida_nacimiento": "no",
        "doc_comprobante_pago": "no",
        "estado": "pendiente",
    }

    if not all([
        solicitud["nombre"],
        solicitud["apellido"],
        solicitud["fecha_nacimiento"],
        solicitud["grado"],
        solicitud["colegio_procedencia"],
    ]):
        print("Error: todos los campos son obligatorios.")
        return

    if not _fecha_valida(solicitud["fecha_nacimiento"]):
        print("Error: fecha invalida. Usa el formato DD/MM/AAAA.")
        return

    solicitudes.append(solicitud)

    print(
        f"Solicitud registrada para {solicitud['nombre']} "
        f"{solicitud['apellido']} (pendiente)."
    )


def marcar_documentos(solicitudes, vacantes):
    dni = input("\nDNI de la solicitud a actualizar: ").strip()
    solicitud = _buscar_por_dni(solicitudes, dni)

    if solicitud is None:
        print("No existe una solicitud con ese DNI.")
        return

    if solicitud["estado"] in (
        "pagada",
        "lista_constancia",
        "matriculado",
    ):
        print("No se pueden modificar documentos en esta etapa.")
        return

    estado_anterior = solicitud["estado"]

    solicitud["doc_dni"] = _pedir_si_no(
        "Trajo DNI? (s/n): "
    )

    solicitud["doc_partida_nacimiento"] = _pedir_si_no(
        "Trajo partida de nacimiento? (s/n): "
    )

    if estado_anterior == "aprobada":
        solicitud["doc_comprobante_pago"] = "no"

        # Se libera el cupo de la aprobacion anterior.
        vacantes[solicitud["grado"]]["disponibles"] += 1

        solicitud["estado"] = "pendiente"

        print(
            "Documentos actualizados. La solicitud vuelve a "
            "'pendiente' y debe validarse nuevamente."
        )

    elif estado_anterior in ("observada", "lista_espera"):
        solicitud["estado"] = "pendiente"

        print(
            "Documentos actualizados. La solicitud vuelve a "
            "'pendiente' para revalidarse."
        )

    else:
        print("Documentos actualizados.")


def ver_estado_solicitudes(solicitudes):
    print("\n-- Estado de las solicitudes --")

    if not solicitudes:
        print("No hay solicitudes registradas.")
        return

    for solicitud in solicitudes:
        print(
            f"{solicitud['dni']} - "
            f"{solicitud['nombre']} {solicitud['apellido']} "
            f"({solicitud['grado']}): {solicitud['estado']}"
        )


def ver_vacantes(solicitudes, vacantes):
    print("\n-- Vacantes por grado --")

    if not vacantes:
        print("No hay vacantes configuradas.")
        return

    for grado, cupos in vacantes.items():
        en_espera = sum(
            1 for s in solicitudes
            if s["grado"] == grado and s["estado"] == "lista_espera"
        )

        print(
            f"{grado}: {cupos['disponibles']} disponible(s) de "
            f"{cupos['totales']} | en lista de espera: {en_espera}"
        )


def registrar_pago(solicitudes):
    dni = input("\nDNI de la solicitud aprobada: ").strip()
    solicitud = _buscar_por_dni(solicitudes, dni)

    if solicitud is None:
        print("No existe una solicitud con ese DNI.")
        return

    if solicitud["estado"] != "aprobada":
        print(
            f"La solicitud esta en estado '{solicitud['estado']}', "
            "no se puede registrar el pago."
        )
        return

    solicitud["doc_comprobante_pago"] = "si"
    solicitud["estado"] = "pagada"

    print("Pago registrado. La solicitud queda en estado 'pagada'.")


def marcar_lista_constancia(solicitudes):
    dni = input("\nDNI de la solicitud pagada: ").strip()
    solicitud = _buscar_por_dni(solicitudes, dni)

    if solicitud is None:
        print("No existe una solicitud con ese DNI.")
        return

    if solicitud["estado"] != "pagada":
        print(
            f"La solicitud esta en estado '{solicitud['estado']}', "
            "no se puede emitir constancia."
        )
        return

    solicitud["estado"] = "lista_constancia"

    print("Solicitud lista para constancia de vacante.")


def registrar_liberacion(solicitudes):
    dni = input(
        "\nDNI del estudiante liberado en SIAGIE: "
    ).strip()

    solicitud = _buscar_por_dni(solicitudes, dni)

    if solicitud is None:
        print("No existe una solicitud con ese DNI.")
        return

    if solicitud["estado"] != "lista_constancia":
        print(
            f"La solicitud esta en estado '{solicitud['estado']}', "
            "aun no corresponde matricular."
        )
        return

    solicitud["estado"] = "matriculado"

    print(
        f"{solicitud['nombre']} {solicitud['apellido']} "
        "queda registrado como matriculado."
    )


# --- Funciones auxiliares ---------------------------------------------------

def _buscar_por_dni(solicitudes, dni):
    for solicitud in solicitudes:
        if solicitud["dni"] == dni:
            return solicitud

    return None


def _fecha_valida(texto):
    try:
        fecha = datetime.strptime(texto, "%d/%m/%Y")
    except ValueError:
        return False

    return fecha <= datetime.now()


def _pedir_grado(vacantes):
    grados = list(vacantes)

    print("Grados disponibles:")
    for numero, grado in enumerate(grados, start=1):
        print(f"  {numero}. {grado}")

    while True:
        respuesta = input("Grado solicitado (numero o nombre): ").strip()

        if respuesta.isdigit() and 1 <= int(respuesta) <= len(grados):
            return grados[int(respuesta) - 1]

        for grado in grados:
            if grado.lower() == respuesta.lower():
                return grado

        print("Grado invalido. Elige uno de la lista.")


def _pedir_si_no(mensaje):
    while True:
        respuesta = input(mensaje).strip().lower()

        if respuesta in ("s", "si", "sí"):
            return "si"

        if respuesta in ("n", "no"):
            return "no"

        print("Respuesta invalida. Escribe s o n.")


# --- Validacion e informacion -----------------------------------------------

def _validar_e_informar(solicitudes, vacantes):
    if not vacantes:
        print(
            "\nNo hay vacantes configuradas. "
            "Revisa el archivo datos/vacantes.csv."
        )
        return

    resultado = validar_solicitudes_pendientes(
        solicitudes,
        vacantes
    )

    print(
        f"\nValidacion terminada: "
        f"{resultado['aprobadas']} aprobada(s), "
        f"{resultado['observadas']} observada(s), "
        f"{resultado['en_espera']} en lista de espera."
    )


# --- Menu principal ---------------------------------------------------------

def menu():
    solicitudes = cargar_solicitudes()
    vacantes = cargar_vacantes()

    opciones = {
        "1": lambda: registrar_solicitud(solicitudes, vacantes),
        "2": lambda: marcar_documentos(solicitudes, vacantes),
        "3": lambda: _validar_e_informar(solicitudes, vacantes),
        "4": lambda: ver_estado_solicitudes(solicitudes),
        "5": lambda: registrar_pago(solicitudes),
        "6": lambda: marcar_lista_constancia(solicitudes),
        "7": lambda: registrar_liberacion(solicitudes),
        "8": lambda: ver_vacantes(solicitudes, vacantes),
    }

    while True:
        print("\n=== Sistema de Matricula - Colegio Peruano de Ciencias ===")
        print("1. Registrar solicitud de matricula")
        print("2. Marcar documentos entregados")
        print("3. Validar solicitudes pendientes")
        print("4. Ver estado de las solicitudes")
        print("5. Registrar pago de una solicitud aprobada")
        print("6. Marcar lista para constancia de vacante")
        print("7. Registrar liberacion SIAGIE y matricular")
        print("8. Ver vacantes por grado")
        print("0. Guardar y salir")

        opcion = input("Elige una opcion: ").strip()

        if opcion == "0":
            guardar_solicitudes(solicitudes)
            guardar_vacantes(vacantes)

            print("Datos guardados. Hasta luego.")
            break

        accion = opciones.get(opcion)

        if accion is None:
            print("Opcion invalida.")
            continue

        accion()

        # Guardado automatico: no se pierde nada si se cierra sin la opcion 0.
        guardar_solicitudes(solicitudes)
        guardar_vacantes(vacantes)


# --- Inicio del programa ----------------------------------------------------

if __name__ == "__main__":
    menu()