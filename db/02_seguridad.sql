SET NAMES utf8mb4;
-- =====================================================================
--  Script 2/3: usuarios de base de datos con permisos diferenciados
--
--  La aplicación nunca se conecta como root. Usa tres usuarios:
--   * tf5_auth       -> solo puede leer la tabla login (para autenticar).
--   * tf5_admin      -> ABM de toda la información del torneo.
--   * tf5_planillero -> solo lectura, salvo planilla/goles/tarjetas y
--                       el estado del partido (para marcarlo jugado).
--  Los triggers corren con los permisos de su DEFINER, por eso el
--  planillero no necesita permisos sobre sancion_jugador para que las
--  sanciones automáticas se generen.
--
--  IMPORTANTE: cambiar estas contraseñas en un entorno real (y en el
--  archivo .env de la aplicación).
-- =====================================================================
USE torneo_futbol5;

DROP USER IF EXISTS 'tf5_auth'@'%', 'tf5_admin'@'%', 'tf5_planillero'@'%';

CREATE USER 'tf5_auth'@'%'       IDENTIFIED BY 'Auth.Tf5.2026';
CREATE USER 'tf5_admin'@'%'      IDENTIFIED BY 'Admin.Tf5.2026';
CREATE USER 'tf5_planillero'@'%' IDENTIFIED BY 'Planillero.Tf5.2026';

-- Autenticación -----------------------------------------------------------
GRANT SELECT ON torneo_futbol5.login TO 'tf5_auth'@'%';

-- Administrador -----------------------------------------------------------
-- No tiene acceso a la tabla login (las cuentas se gestionan aparte).
GRANT SELECT, INSERT, UPDATE, DELETE ON torneo_futbol5.facultad              TO 'tf5_admin'@'%';
GRANT SELECT, INSERT, UPDATE, DELETE ON torneo_futbol5.jugador               TO 'tf5_admin'@'%';
GRANT SELECT, INSERT, UPDATE, DELETE ON torneo_futbol5.torneo                TO 'tf5_admin'@'%';
GRANT SELECT, INSERT, UPDATE, DELETE ON torneo_futbol5.equipo                TO 'tf5_admin'@'%';
GRANT SELECT, INSERT, UPDATE, DELETE ON torneo_futbol5.equipo_jugador_torneo TO 'tf5_admin'@'%';
GRANT SELECT, INSERT, UPDATE, DELETE ON torneo_futbol5.complejo              TO 'tf5_admin'@'%';
GRANT SELECT, INSERT, UPDATE, DELETE ON torneo_futbol5.cancha                TO 'tf5_admin'@'%';
GRANT SELECT                         ON torneo_futbol5.turno                 TO 'tf5_admin'@'%';
GRANT SELECT, INSERT, UPDATE, DELETE ON torneo_futbol5.partido               TO 'tf5_admin'@'%';
GRANT SELECT, INSERT, DELETE         ON torneo_futbol5.planilla_partido      TO 'tf5_admin'@'%';
GRANT SELECT, INSERT, DELETE         ON torneo_futbol5.gol                   TO 'tf5_admin'@'%';
GRANT SELECT, INSERT, DELETE         ON torneo_futbol5.tarjeta               TO 'tf5_admin'@'%';
GRANT SELECT, INSERT, UPDATE, DELETE ON torneo_futbol5.sancion_jugador       TO 'tf5_admin'@'%';
GRANT SELECT ON torneo_futbol5.v_resultado_partido TO 'tf5_admin'@'%';
GRANT SELECT ON torneo_futbol5.v_partido_equipo    TO 'tf5_admin'@'%';
GRANT SELECT ON torneo_futbol5.v_tabla_posiciones  TO 'tf5_admin'@'%';
GRANT SELECT ON torneo_futbol5.v_goleadores        TO 'tf5_admin'@'%';
GRANT SELECT ON torneo_futbol5.v_fair_play         TO 'tf5_admin'@'%';
GRANT SELECT ON torneo_futbol5.v_sancion_detalle   TO 'tf5_admin'@'%';
GRANT EXECUTE ON FUNCTION torneo_futbol5.fn_jugador_suspendido TO 'tf5_admin'@'%';
GRANT EXECUTE ON FUNCTION torneo_futbol5.fn_tamano_plantel     TO 'tf5_admin'@'%';
GRANT EXECUTE ON FUNCTION torneo_futbol5.fn_ci_valida          TO 'tf5_admin'@'%';

-- Planillero --------------------------------------------------------------
GRANT SELECT ON torneo_futbol5.facultad              TO 'tf5_planillero'@'%';
GRANT SELECT ON torneo_futbol5.jugador               TO 'tf5_planillero'@'%';
GRANT SELECT ON torneo_futbol5.torneo                TO 'tf5_planillero'@'%';
GRANT SELECT ON torneo_futbol5.equipo                TO 'tf5_planillero'@'%';
GRANT SELECT ON torneo_futbol5.equipo_jugador_torneo TO 'tf5_planillero'@'%';
GRANT SELECT ON torneo_futbol5.complejo              TO 'tf5_planillero'@'%';
GRANT SELECT ON torneo_futbol5.cancha                TO 'tf5_planillero'@'%';
GRANT SELECT ON torneo_futbol5.turno                 TO 'tf5_planillero'@'%';
GRANT SELECT ON torneo_futbol5.sancion_jugador       TO 'tf5_planillero'@'%';
GRANT SELECT ON torneo_futbol5.v_resultado_partido   TO 'tf5_planillero'@'%';
-- Del partido solo puede modificar la columna estado (privilegio por columna).
GRANT SELECT, UPDATE (estado) ON torneo_futbol5.partido TO 'tf5_planillero'@'%';
GRANT SELECT, INSERT, DELETE ON torneo_futbol5.planilla_partido TO 'tf5_planillero'@'%';
GRANT SELECT, INSERT, DELETE ON torneo_futbol5.gol              TO 'tf5_planillero'@'%';
GRANT SELECT, INSERT, DELETE ON torneo_futbol5.tarjeta          TO 'tf5_planillero'@'%';
GRANT EXECUTE ON FUNCTION torneo_futbol5.fn_jugador_suspendido TO 'tf5_planillero'@'%';

FLUSH PRIVILEGES;
