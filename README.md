# Torneo Interfacultades de Fútbol 5 — UCU

Sistema de gestión del Torneo Interfacultades de Fútbol 5 (Base de Datos 1, Obligatorio 2.º semestre 2026).

- **Backend:** Python 3.10+ con Flask, sin ORM (SQL escrito a mano con `mysql-connector-python` y consultas parametrizadas).
- **Base de datos:** MySQL 8.0, con las reglas de negocio implementadas en la propia base (CHECK, claves foráneas compuestas, triggers, procedimientos y vistas).
- **Frontend:** plantillas HTML (Jinja2) servidas por Flask, con CSS y JavaScript propios (sin frameworks).
- **Seguridad:** tres usuarios de base de datos con permisos diferenciados (autenticación, administrador y planillero), contraseñas hasheadas (PBKDF2), protección CSRF y validación en las tres capas.

---

## 1. Estructura del proyecto

```
torneo-futbol5/
├── docker-compose.yml        # servicios db (MySQL 8) y app (Flask + gunicorn)
├── script_completo.sql       # 01 + 02 + 03 concatenados (para correrlo de una sola vez)
├── db/
│   ├── 01_esquema.sql        # base, tablas, restricciones, funciones, procedimientos, triggers y vistas
│   ├── 02_seguridad.sql      # usuarios de BD tf5_auth, tf5_admin y tf5_planillero con sus permisos
│   └── 03_datos.sql          # datos maestros y de prueba (8 equipos, fechas 1-3 jugadas, fecha 4 en curso)
├── herramientas/
│   └── generar_datos.py      # script que generó 03_datos.sql (no hace falta ejecutarlo)
└── app/
    ├── app.py                # punto de entrada (Flask)
    ├── config.py             # configuración por variables de entorno
    ├── db.py                 # conexión por rol, ejecución de SQL y traducción de errores
    ├── seguridad.py          # login, control de roles y CSRF
    ├── validaciones.py       # validación de formularios en el backend
    ├── comun.py              # utilidades compartidas
    ├── routes/               # una "blueprint" por módulo (jugadores, equipos, partidos, planillas, ...)
    ├── templates/            # vistas HTML
    ├── static/               # estilos.css y app.js (validación en el navegador)
    ├── requirements.txt
    └── Dockerfile
```

## 2. Usuarios de prueba

| Rol | Correo | Contraseña |
|---|---|---|
| Administrador | `admin@ucu.edu.uy` | `Admin123!` |
| Planillero | `planillero@ucu.edu.uy` | `Planillero123!` |
| Planillero | `planillero2@ucu.edu.uy` | `Planillero123!` |

Usuarios de **base de datos** (los usa la aplicación, definidos en `db/02_seguridad.sql`):

| Usuario MySQL | Contraseña | Uso |
|---|---|---|
| `tf5_auth` | `Auth.Tf5.2026` | Solo lectura de la tabla `login` para autenticar |
| `tf5_admin` | `Admin.Tf5.2026` | ABM de toda la información del torneo (sin acceso a `login`) |
| `tf5_planillero` | `Planillero.Tf5.2026` | Lectura; escritura solo en planilla, goles, tarjetas y la columna `estado` del partido |

---

## 3. Opción A — Correr con Docker (recomendado)

Requisitos: Docker Desktop (o Docker Engine + Compose v2).

```bash
cd torneo-futbol5
docker compose up --build
```

1. La primera vez MySQL ejecuta automáticamente `db/01_esquema.sql`, `db/02_seguridad.sql` y `db/03_datos.sql` (tarda ~30 s).
2. La aplicación espera a que la base esté lista (healthcheck) y queda disponible en **http://localhost:8000**.
3. Ingresar con alguno de los usuarios de la tabla anterior.

Comandos útiles:

```bash
docker compose down          # detener
docker compose down -v       # detener y BORRAR la base (la próxima vez se vuelve a cargar desde los scripts)
docker compose logs -f app   # ver logs de la aplicación
```

> La base queda expuesta en el puerto **3307** del host (para conectarse con MySQL Workbench: `127.0.0.1:3307`, usuario `root`, contraseña `root.Tf5.2026`).

---

## 4. Opción B — Correr localmente sin Docker

Requisitos: **MySQL Server 8.0** y **Python 3.10 o superior**.

### 4.1 Crear la base de datos

Con la terminal (Linux / macOS / Git Bash):

```bash
mysql -u root -p < script_completo.sql
```

En Windows (PowerShell no admite `<`):

```powershell
mysql -u root -p -e "source script_completo.sql"
```

O con **MySQL Workbench**: *File → Open SQL Script* → `script_completo.sql` → ejecutar todo (⚡).

El script borra y recrea la base `torneo_futbol5`, crea los tres usuarios de base de datos y carga los datos de prueba.

### 4.2 Instalar y ejecutar la aplicación

```bash
cd app
python -m venv .venv
# Linux / macOS:
source .venv/bin/activate
# Windows:
.venv\Scripts\activate

pip install -r requirements.txt
python app.py
```

Abrir **http://localhost:5000**.

Los valores por defecto de la configuración coinciden con los scripts SQL (MySQL en `127.0.0.1:3306`). Si MySQL corre en otro puerto u host, definir las variables de entorno antes de `python app.py` (ver `.env.example`), por ejemplo:

```bash
export DB_PORT=3307            # Windows PowerShell:  $env:DB_PORT="3307"
```

---

## 5. Recorrido sugerido para la demo

Los datos de prueba se generan **relativos a la fecha en que se ejecuta el script**, así siempre hay casos para mostrar:

1. **Inicio** (admin): resumen de la edición 2026/2, top 5 y próximos partidos.
2. **Planillas → partido de la fecha 4 "Pendiente de planilla"** (jugado hace 2 días, sin planilla): marcar jugadores (una jugadora aparece *Suspendida* por sanción disciplinaria y no se puede elegir), cargar goles y tarjetas y **Marcar partido como jugado**.
   - Una tarjeta roja genera automáticamente la suspensión para la fecha siguiente (ver **Sanciones**).
3. **Planillas → partido de la fecha 4 jugado ayer**: se puede corregir (está dentro de las 48 h).
4. **Planillas → cualquier partido de las fechas 1 a 3**: ya no se puede corregir (pasaron más de 48 h).
5. **Partidos**: intentar programar un cruce que ya existe, un equipo dos veces en la misma fecha o una cancha ocupada → la base lo rechaza con un mensaje claro. El partido cancelado de la fecha 4 permite volver a programar ese cruce. El partido postergado de la fecha 3 se puede reprogramar.
6. **Equipos**: con el torneo *En curso* los planteles no se pueden modificar. Crear una edición nueva en **Torneos** para probar altas de equipos/planteles (máximo 10 jugadores, máximo 2 docentes/funcionarios, misma facultad) y el **generador automático de fixture**.
7. **Reportes**: todos los reportes pedidos + 3 consultas adicionales, cada uno con su consulta SQL visible.
8. Ingresar como **planillero**: solo ve el módulo de planillas; cualquier otra URL devuelve 403 y, aunque se saltara la aplicación, el usuario de base `tf5_planillero` no tiene permisos para modificar otra cosa.

---

## 6. Reglas de negocio y dónde se controlan

| Regla | Base de datos | Backend | Frontend |
|---|---|---|---|
| Capitán es jugador del plantel | FK compuesta `equipo(id_equipo, ci_capitan) → plantel` | select limitado al plantel | select |
| Plantel de 5 a 10, máx. 2 docentes/funcionarios, misma facultad | triggers `trg_plantel_bi`, `trg_torneo_bu` | — | indicadores |
| Un jugador en un solo equipo por edición | `UNIQUE (ci_jugador, id_torneo)` | candidatos filtrados | — |
| Planteles solo en inscripción | `sp_exigir_inscripcion` (triggers) | botones ocultos | — |
| Partido: misma edición, ≥5 jugadores, sin auto-enfrentamiento | FK compuestas + `CHECK` + `sp_validar_partido` | validación | equipos incompletos deshabilitados, JS local≠visitante |
| Cruce único salvo cancelado | `UNIQUE` sobre columnas generadas `equipo_menor/equipo_mayor/vigente` | — | — |
| Un partido por equipo y fecha | `sp_validar_partido` | — | — |
| Cancha: un partido por día y turno | `UNIQUE` con columna generada `ocupa_cancha` | — | — |
| Planilla solo con jugadores del plantel, no suspendidos | FK compuesta + `trg_planilla_bi` | lista filtrada | suspendidos deshabilitados |
| Goles y tarjetas solo de jugadores en planilla | FK compuesta `(id_partido, ci_jugador) → planilla` | select limitado | select |
| Jugado solo si el turno ya pasó | `trg_partido_bu` | botón condicionado | — |
| Partido jugado no se elimina; corrección solo 48 h | `trg_partido_bd`, `sp_validar_ventana_planilla` | edición deshabilitada | — |
| Sanción automática (roja / 3 amarillas) | `trg_tarjeta_ai/ad`, `sp_recalcular_amarillas` | — | — |
| Cédula uruguaya válida | `fn_ci_valida` + `CHECK` | `ci_valida()` | `app.js` |

---

## 7. Problemas frecuentes

- **"No se pudo conectar con la base de datos"**: verificar que MySQL esté levantado y que se haya ejecutado `02_seguridad.sql` (crea los usuarios `tf5_*`).
- **Puerto 5000 ocupado en macOS** (AirPlay): ejecutar `flask --app app run --port 5050` o usar Docker (puerto 8000).
- **Horarios corridos**: la aplicación fija la zona horaria de la sesión de MySQL en `-03:00` (`DB_TIME_ZONE`), por lo que las reglas de "turno ya pasó" y "48 horas" usan la hora de Uruguay aunque el servidor esté en UTC.
- **Volver a los datos iniciales**: ejecutar nuevamente `script_completo.sql` (o `docker compose down -v && docker compose up`).
