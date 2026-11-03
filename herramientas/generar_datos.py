"""
Genera db/03_datos.sql con datos maestros y de prueba.

No es necesario ejecutarlo para usar el sistema (el .sql ya viene generado);
se incluye para documentar cómo se construyeron los datos y poder
regenerarlos. Simula las sanciones automáticas para que ningún jugador
suspendido figure en una planilla (la base lo rechazaría).

Uso:  python herramientas/generar_datos.py
"""
import random
from pathlib import Path

from werkzeug.security import generate_password_hash

random.seed(2026)
SALIDA = Path(__file__).resolve().parent.parent / "db" / "03_datos.sql"

NOMBRES = ["Martín", "Santiago", "Matías", "Nicolás", "Facundo", "Agustín", "Joaquín", "Diego",
           "Federico", "Gonzalo", "Rodrigo", "Sebastián", "Lucas", "Bruno", "Emiliano", "Franco",
           "Ignacio", "Juan", "Pablo", "Tomás", "Valentín", "Maximiliano", "Andrés", "Felipe",
           "Lucía", "Sofía", "Valentina", "Camila", "Florencia", "Carolina", "Micaela", "Agustina"]
APELLIDOS = ["Rodríguez", "González", "Fernández", "Silva", "Pereira", "Martínez", "Sosa", "López",
             "Díaz", "Méndez", "Suárez", "Núñez", "Castro", "Romero", "Álvarez", "Benítez",
             "Acosta", "Cabrera", "Olivera", "Ramírez", "Techera", "Correa", "Viera", "Píriz",
             "Cardozo", "Morales", "De León", "Ferreira", "Machado", "Bentancur", "Giménez", "Da Silva"]

FACULTADES = ["Facultad de Ingeniería y Tecnologías", "Facultad de Ciencias Empresariales",
              "Facultad de Derecho", "Facultad de Ciencias de la Salud",
              "Facultad de Ciencias Humanas", "Facultad de Psicología"]

# (nombre, id_facultad, tamaño del plantel, cantidad de docentes/funcionarios)
EQUIPOS = [("Los Compiladores", 1, 9, 2), ("Bits FC", 1, 7, 1),
           ("Balance General", 2, 8, 1), ("Activo Corriente", 2, 7, 0),
           ("Jurisprudencia FC", 3, 8, 2), ("Bisturí FC", 4, 7, 1),
           ("Dialéctica United", 5, 6, 0), ("Inconsciente Colectivo", 6, 8, 1)]

COMPLEJOS = [("Complejo Pocitos Fútbol 5", "Av. Brasil 2850", "Montevideo",
              [("Cancha 1", "sintetico", 0), ("Cancha 2", "sintetico", 1)]),
             ("Arena Carrasco", "Av. Italia 6201", "Montevideo",
              [("Central", "parquet", 1), ("Norte", "sintetico", 0)]),
             ("Club Ciudad de la Costa", "Av. Giannattasio km 21", "Canelones",
              [("Cancha A", "sintetico", 0)])]
CANCHAS = [(i + 1, c[0]) for i, comp in enumerate(COMPLEJOS) for c in comp[3]]


def ci_valida(base: int) -> str:
    base7 = f"{base:07d}"
    suma = sum(int(d) * int(p) for d, p in zip(base7, "2987634"))
    return base7 + str((10 - suma % 10) % 10)


def q(v):
    if v is None:
        return "NULL"
    if isinstance(v, bool):
        return "TRUE" if v else "FALSE"
    if isinstance(v, (int, float)):
        return str(v)
    if isinstance(v, Raw):
        return v.sql
    return "'" + str(v).replace("'", "''") + "'"


class Raw:
    def __init__(self, sql):
        self.sql = sql


def insert(tabla, columnas, filas):
    vals = ",\n    ".join("(" + ", ".join(q(v) for v in f) + ")" for f in filas)
    return f"INSERT INTO {tabla} ({', '.join(columnas)}) VALUES\n    {vals};\n"


out = []
w = out.append
w("-- =====================================================================\n"
  "--  Script 3/3: datos maestros y datos de prueba\n"
  "--  Generado con herramientas/generar_datos.py\n"
  "--  8 equipos, fechas 1 a 3 disputadas (una postergada), fecha 4 en curso\n"
  "--  y fecha 5 programada. Las fechas de la fecha 4 y 5 se calculan respecto\n"
  "--  a CURDATE() para que siempre haya un partido recién jugado (corregible\n"
  "--  dentro de 48 h), uno pendiente de planilla y partidos futuros.\n"
  "--  Las sanciones por roja/amarillas las generan los triggers.\n"
  "-- =====================================================================\n"
  "USE torneo_futbol5;\n\n")

# ---- Usuarios de la aplicación -------------------------------------------
w("-- Usuarios de la aplicación (contraseñas: Admin123! / Planillero123!)\n")
w(insert("login", ["correo", "contrasena", "rol"], [
    ("admin@ucu.edu.uy", generate_password_hash("Admin123!", method="pbkdf2:sha256"), "administrador"),
    ("planillero@ucu.edu.uy", generate_password_hash("Planillero123!", method="pbkdf2:sha256"), "planillero"),
    ("planillero2@ucu.edu.uy", generate_password_hash("Planillero123!", method="pbkdf2:sha256"), "planillero"),
]))

# ---- Datos maestros --------------------------------------------------------
w("\n-- Datos maestros\n")
w(insert("facultad", ["id_facultad", "nombre"], [(i + 1, n) for i, n in enumerate(FACULTADES)]))
w(insert("turno", ["id_turno", "hora_inicio", "hora_fin"],
         [(i + 1, f"{h}:00:00", f"{h + 1}:00:00") for i, h in enumerate(range(18, 23))]))
w(insert("complejo", ["id_complejo", "nombre", "direccion", "departamento"],
         [(i + 1, c[0], c[1], c[2]) for i, c in enumerate(COMPLEJOS)]))
w(insert("cancha", ["id_complejo", "nombre_cancha", "superficie", "techada"],
         [(i + 1, n, s, bool(t)) for i, comp in enumerate(COMPLEJOS) for (n, s, t) in comp[3]]))

# ---- Jugadores -------------------------------------------------------------
jugadores = []          # dicts
usados = set()
base_ci = 4_100_000


def nuevo_jugador(id_fac, tipo):
    global base_ci
    base_ci += random.randint(1_000, 60_000)
    while True:
        n, a = random.choice(NOMBRES), random.choice(APELLIDOS)
        if (n, a) not in usados:
            usados.add((n, a))
            break
    ci = ci_valida(base_ci)
    anio = random.randint(1970, 1990) if tipo in ("docente", "funcionario") else random.randint(1998, 2007)
    email = (f"{n}.{a}".lower().replace(" ", "")
             .translate(str.maketrans("áéíóúñ", "aeioun")) + "@correo.ucu.edu.uy")
    j = dict(ci=ci, nombre=n, apellido=a, email=email,
             fnac=f"{anio}-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}",
             fac=id_fac, tipo=tipo)
    jugadores.append(j)
    return j


planteles = []          # (id_equipo, [jugadores])
for idx, (nombre, fac, tam, doc) in enumerate(EQUIPOS, start=1):
    miembros = []
    for k in range(tam):
        if k < doc:
            tipo = random.choice(["docente", "funcionario"])
        else:
            tipo = "posgrado" if random.random() < 0.15 else "grado"
        miembros.append(nuevo_jugador(fac, tipo))
    planteles.append((idx, miembros))

# Jugadores registrados que no integran ningún plantel (para ABM y reportes)
for fac in range(1, 7):
    for _ in range(2):
        nuevo_jugador(fac, random.choice(["grado", "grado", "posgrado", "docente", "funcionario"]))

w("\n-- Jugadores\n")
w(insert("jugador", ["ci", "nombre", "apellido", "email", "fecha_nacimiento", "id_facultad", "tipo"],
         [(j["ci"], j["nombre"], j["apellido"], j["email"], j["fnac"], j["fac"], j["tipo"]) for j in jugadores]))

# ---- Torneo, equipos y planteles -------------------------------------------
w("\n-- Torneo (se crea en inscripción, se cargan los planteles y luego pasa a en curso)\n")
w("INSERT INTO torneo (id_torneo, nombre, anio, semestre, fecha_inicio, fecha_fin) VALUES\n"
  "    (1, 'Torneo Interfacultades de Fútbol 5 - 2026/2', 2026, 2, '2026-08-17',\n"
  "     GREATEST('2026-12-11', CURDATE() + INTERVAL 60 DAY));\n")
w(insert("equipo", ["id_equipo", "nombre", "id_torneo", "id_facultad"],
         [(i, e[0], 1, e[1]) for i, e in enumerate(EQUIPOS, start=1)]))
filas = []
for id_eq, miembros in planteles:
    camisetas = random.sample(range(1, 24), len(miembros))
    filas += [(id_eq, j["ci"], 1, c) for j, c in zip(miembros, camisetas)]
w(insert("equipo_jugador_torneo", ["id_equipo", "ci_jugador", "id_torneo", "numero_camiseta"], filas))
for id_eq, miembros in planteles:
    cap = miembros[len(miembros) // 2]
    w(f"UPDATE equipo SET ci_capitan = '{cap['ci']}' WHERE id_equipo = {id_eq};\n")
w("UPDATE torneo SET estado = 'en_curso' WHERE id_torneo = 1;\n")

# ---- Fixture (método del círculo) ------------------------------------------
equipos_ids = [e for e, _ in planteles]


def round_robin(ids):
    ids = ids[:]
    fechas = []
    for f in range(len(ids) - 1):
        pares = []
        for i in range(len(ids) // 2):
            a, b = ids[i], ids[-1 - i]
            pares.append((a, b) if (f + i) % 2 == 0 else (b, a))
        fechas.append(pares)
        ids = [ids[0]] + [ids[-1]] + ids[1:-1]
    return fechas


fixture = round_robin(equipos_ids)

DIAS_FIJOS = {1: ["2026-09-14", "2026-09-15", "2026-09-16", "2026-09-17"],
              2: ["2026-09-28", "2026-09-29", "2026-09-30", "2026-10-01"],
              3: ["2026-10-12", "2026-10-13", "2026-10-14", "2026-10-15"]}
DIAS_DINAMICOS = {4: ["CURDATE() - INTERVAL 1 DAY", "CURDATE() - INTERVAL 2 DAY",
                      "CURDATE() + INTERVAL 3 DAY", "CURDATE() + INTERVAL 4 DAY"],
                  5: ["CURDATE() + INTERVAL 10 DAY", "CURDATE() + INTERVAL 10 DAY",
                      "CURDATE() + INTERVAL 11 DAY", "CURDATE() + INTERVAL 11 DAY"]}

# Destino de cada partido creado: jugado / postergado / cancelado / pendiente
DESTINO = {(3, 3): "postergado", (4, 0): "jugado", (4, 1): "pendiente",
           (4, 2): "cancelado", (4, 3): "futuro"}
for k in range(4):
    DESTINO.setdefault((1, k), "jugado")
    DESTINO.setdefault((2, k), "jugado")
    DESTINO.setdefault((3, k), "jugado")
    DESTINO.setdefault((5, k), "futuro")

partidos = []   # dicts
id_p = 0
for fecha in range(1, 6):
    for k, (loc, vis) in enumerate(fixture[fecha - 1]):
        id_p += 1
        if fecha in DIAS_FIJOS:
            dia = DIAS_FIJOS[fecha][k]
        else:
            dia = Raw(DIAS_DINAMICOS[fecha][k])
        comp, cancha = CANCHAS[(k + fecha) % len(CANCHAS)]
        turno = 1 + (k + 2 * fecha) % 5 if fecha in DIAS_FIJOS else 1 + k % 2
        partidos.append(dict(id=id_p, fecha=fecha, loc=loc, vis=vis, dia=dia, turno=turno,
                             comp=comp, cancha=cancha, destino=DESTINO[(fecha, k)]))

w("\n-- Fixture: fechas 1 a 5 (se crean como programados)\n")
w(insert("partido", ["id_partido", "id_torneo", "numero_fecha", "id_equipo_local", "id_equipo_visitante",
                     "dia", "id_turno", "id_complejo", "nombre_cancha"],
         [(p["id"], 1, p["fecha"], p["loc"], p["vis"], p["dia"], p["turno"], p["comp"], p["cancha"])
          for p in partidos]))

# ---- Simulación de partidos jugados -----------------------------------------
plantel_de = {e: m for e, m in planteles}
# Jugadores que nunca juegan (último de algunos planteles)
nunca_juegan = {plantel_de[1][-1]["ci"], plantel_de[3][-1]["ci"], plantel_de[5][-1]["ci"],
                plantel_de[8][-1]["ci"]}
suspensiones = {}          # ci -> set(fechas)
amarillas = {}             # ci -> cantidad
DISCIPLINARIA = plantel_de[4][2]    # sanción disciplinaria fechas 4 y 5
suspensiones.setdefault(DISCIPLINARIA["ci"], set()).update({4, 5})

# Eventos forzados para que los reportes y las sanciones tengan casos
FORZADO_ROJA = {(1, 0): plantel_de[fixture[0][0][0]][1]["ci"],
                (3, 1): plantel_de[fixture[2][1][1]][2]["ci"]}
FORZADO_AMARILLAS = plantel_de[fixture[2][0][0]][3]["ci"]   # recibe amarilla en fechas 1, 2 y 3

w("\n-- Sanción disciplinaria (cargada por la organización antes de la fecha 4)\n")
w(insert("sancion_jugador", ["ci_jugador", "id_torneo", "motivo", "numero_fecha_inicio",
                             "cantidad_fechas", "observaciones"],
         [(DISCIPLINARIA["ci"], 1, "disciplinaria", 4, 2, "Agresión verbal al árbitro en la fecha 3")]))

w("\n-- Planillas, goles y tarjetas de los partidos disputados\n")
for p in partidos:
    if p["destino"] not in ("jugado",):
        continue
    planilla = {}
    key = (p["fecha"], [x["id"] for x in partidos if x["fecha"] == p["fecha"]].index(p["id"]))
    forzados = {FORZADO_AMARILLAS, FORZADO_ROJA.get(key)}
    for eq in (p["loc"], p["vis"]):
        disponibles = [j for j in plantel_de[eq]
                       if p["fecha"] not in suspensiones.get(j["ci"], set()) and j["ci"] not in nunca_juegan]
        forz = [j for j in disponibles if j["ci"] in forzados]
        resto = [j for j in disponibles if j["ci"] not in forzados]
        elegidos = forz + random.sample(resto, min(len(resto), random.randint(5, 7) - len(forz)))
        planilla[eq] = elegidos
    filas = [(p["id"], j["ci"], eq) for eq, js in planilla.items() for j in js]
    w(insert("planilla_partido", ["id_partido", "ci_jugador", "id_equipo"], filas))

    goles = []
    for eq in (p["loc"], p["vis"]):
        for _ in range(random.choices([0, 1, 2, 3, 4, 5, 6], [8, 14, 18, 16, 10, 5, 2])[0]):
            goles.append((p["id"], random.choice(planilla[eq])["ci"], random.randint(1, 50), False))
    if p["id"] == 6:   # un autogol para mostrar el cálculo
        rival = p["vis"]
        goles.append((p["id"], planilla[rival][0]["ci"], 33, True))
    if goles:
        w(insert("gol", ["id_partido", "ci_jugador", "minuto", "autogol"], goles))

    tarjetas = []
    ya = set()
    if key in FORZADO_ROJA and FORZADO_ROJA[key] in [j["ci"] for js in planilla.values() for j in js]:
        ci = FORZADO_ROJA[key]
        tarjetas.append((p["id"], ci, random.randint(10, 48), "roja"))
        ya.add(ci)
    for js in planilla.values():
        for j in js:
            if j["ci"] == FORZADO_AMARILLAS and j["ci"] not in ya:
                tarjetas.append((p["id"], j["ci"], random.randint(5, 45), "amarilla"))
                ya.add(j["ci"])
    for js in planilla.values():
        for j in js:
            if j["ci"] in ya:
                continue
            r = random.random()
            if r < 0.10:
                tarjetas.append((p["id"], j["ci"], random.randint(1, 50), "amarilla"))
                ya.add(j["ci"])
            elif r < 0.115:
                tarjetas.append((p["id"], j["ci"], random.randint(1, 50), "roja"))
                ya.add(j["ci"])
    if tarjetas:
        w(insert("tarjeta", ["id_partido", "ci_jugador", "minuto", "color"], tarjetas))
    # Simular las sanciones que generará la base
    for (_, ci, _, color) in tarjetas:
        if color == "roja":
            suspensiones.setdefault(ci, set()).add(p["fecha"] + 1)
        else:
            amarillas[ci] = amarillas.get(ci, 0) + 1
            if amarillas[ci] % 3 == 0:
                suspensiones.setdefault(ci, set()).add(p["fecha"] + 1)
    w(f"UPDATE partido SET estado = 'jugado' WHERE id_partido = {p['id']};\n\n")

w("-- Partidos postergados y cancelados\n")
for p in partidos:
    if p["destino"] == "postergado":
        w(f"UPDATE partido SET estado = 'postergado' WHERE id_partido = {p['id']};\n")
    if p["destino"] == "cancelado":
        w(f"UPDATE partido SET estado = 'cancelado' WHERE id_partido = {p['id']};\n")

SALIDA.write_text("".join(out), encoding="utf-8")
print(f"Generado {SALIDA} ({len(jugadores)} jugadores, {len(partidos)} partidos)")
