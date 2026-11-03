SET NAMES utf8mb4;
-- =====================================================================
--  Torneo Interfacultades de Fútbol 5 - UCU
--  Base de Datos 1 - Obligatorio Segundo Semestre 2026
--  Script 1/3: creación de la base, tablas, restricciones, funciones,
--              procedimientos, triggers y vistas.
--  Motor: MySQL 8.0
-- =====================================================================

DROP DATABASE IF EXISTS torneo_futbol5;
CREATE DATABASE torneo_futbol5
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_0900_ai_ci;
USE torneo_futbol5;

-- ---------------------------------------------------------------------
--  TABLAS
-- ---------------------------------------------------------------------

-- Usuarios de la aplicación. La contraseña se guarda hasheada (PBKDF2),
-- nunca en texto plano.
CREATE TABLE login (
    correo      VARCHAR(100) NOT NULL,
    contrasena  VARCHAR(255) NOT NULL,
    rol         ENUM('administrador', 'planillero') NOT NULL,
    activo      BOOLEAN NOT NULL DEFAULT TRUE,
    CONSTRAINT pk_login PRIMARY KEY (correo),
    CONSTRAINT chk_login_correo CHECK (correo REGEXP '^[^@[:space:]]+@[^@[:space:]]+\\.[^@[:space:]]+$'),
    CONSTRAINT chk_login_hash   CHECK (CHAR_LENGTH(contrasena) >= 20)
);

CREATE TABLE facultad (
    id_facultad INT AUTO_INCREMENT,
    nombre      VARCHAR(100) NOT NULL,
    CONSTRAINT pk_facultad PRIMARY KEY (id_facultad),
    CONSTRAINT uq_facultad_nombre UNIQUE (nombre),
    CONSTRAINT chk_facultad_nombre CHECK (CHAR_LENGTH(TRIM(nombre)) >= 3)
);

-- La CI se guarda sin puntos ni guion, incluyendo el dígito verificador.
-- El dígito verificador se controla con fn_ci_valida (trigger).
CREATE TABLE jugador (
    ci               VARCHAR(8)   NOT NULL,
    nombre           VARCHAR(50)  NOT NULL,
    apellido         VARCHAR(50)  NOT NULL,
    email            VARCHAR(100) NOT NULL,
    fecha_nacimiento DATE         NOT NULL,
    id_facultad      INT          NOT NULL,
    tipo             ENUM('grado', 'posgrado', 'docente', 'funcionario') NOT NULL,
    CONSTRAINT pk_jugador PRIMARY KEY (ci),
    CONSTRAINT uq_jugador_email UNIQUE (email),
    CONSTRAINT fk_jugador_facultad FOREIGN KEY (id_facultad) REFERENCES facultad (id_facultad),
    CONSTRAINT chk_jugador_ci       CHECK (ci REGEXP '^[0-9]{7,8}$'),
    CONSTRAINT chk_jugador_nombre   CHECK (CHAR_LENGTH(TRIM(nombre)) >= 2),
    CONSTRAINT chk_jugador_apellido CHECK (CHAR_LENGTH(TRIM(apellido)) >= 2),
    CONSTRAINT chk_jugador_email    CHECK (email REGEXP '^[^@[:space:]]+@[^@[:space:]]+\\.[^@[:space:]]+$'),
    CONSTRAINT chk_jugador_fnac     CHECK (fecha_nacimiento >= '1920-01-01')
);

-- Cada edición del torneo corresponde a un semestre (anio + semestre único).
CREATE TABLE torneo (
    id_torneo    INT AUTO_INCREMENT,
    nombre       VARCHAR(100) NOT NULL,
    anio         SMALLINT     NOT NULL,
    semestre     TINYINT      NOT NULL,
    fecha_inicio DATE         NOT NULL,
    fecha_fin    DATE         NOT NULL,
    estado       ENUM('inscripcion', 'en_curso', 'finalizado') NOT NULL DEFAULT 'inscripcion',
    CONSTRAINT pk_torneo PRIMARY KEY (id_torneo),
    CONSTRAINT uq_torneo_edicion UNIQUE (anio, semestre),
    CONSTRAINT chk_torneo_semestre CHECK (semestre IN (1, 2)),
    CONSTRAINT chk_torneo_anio     CHECK (anio BETWEEN 2000 AND 2100),
    CONSTRAINT chk_torneo_fechas   CHECK (fecha_fin > fecha_inicio),
    CONSTRAINT chk_torneo_nombre   CHECK (CHAR_LENGTH(TRIM(nombre)) >= 3)
);

-- El capitán se referencia contra el plantel (FK compuesta más abajo),
-- así la base garantiza que el capitán es uno de sus jugadores.
CREATE TABLE equipo (
    id_equipo   INT AUTO_INCREMENT,
    nombre      VARCHAR(60) NOT NULL,
    id_torneo   INT         NOT NULL,
    id_facultad INT         NOT NULL,
    ci_capitan  VARCHAR(8)  NULL,
    CONSTRAINT pk_equipo PRIMARY KEY (id_equipo),
    CONSTRAINT uq_equipo_nombre UNIQUE (id_torneo, nombre),
    CONSTRAINT uq_equipo_torneo UNIQUE (id_equipo, id_torneo),
    CONSTRAINT fk_equipo_torneo   FOREIGN KEY (id_torneo)   REFERENCES torneo (id_torneo),
    CONSTRAINT fk_equipo_facultad FOREIGN KEY (id_facultad) REFERENCES facultad (id_facultad),
    CONSTRAINT chk_equipo_nombre  CHECK (CHAR_LENGTH(TRIM(nombre)) >= 2)
);

-- Plantel. id_torneo se repite (desnormalización controlada) para poder
-- imponer con UNIQUE que un jugador integre un solo equipo por edición.
CREATE TABLE equipo_jugador_torneo (
    id_equipo       INT              NOT NULL,
    ci_jugador      VARCHAR(8)       NOT NULL,
    id_torneo       INT              NOT NULL,
    numero_camiseta TINYINT UNSIGNED NOT NULL,
    CONSTRAINT pk_plantel PRIMARY KEY (id_equipo, ci_jugador),
    CONSTRAINT uq_plantel_jugador_torneo UNIQUE (ci_jugador, id_torneo),
    CONSTRAINT uq_plantel_camiseta UNIQUE (id_equipo, numero_camiseta),
    CONSTRAINT fk_plantel_equipo  FOREIGN KEY (id_equipo, id_torneo) REFERENCES equipo (id_equipo, id_torneo) ON DELETE CASCADE,
    CONSTRAINT fk_plantel_jugador FOREIGN KEY (ci_jugador) REFERENCES jugador (ci),
    CONSTRAINT chk_plantel_camiseta CHECK (numero_camiseta BETWEEN 1 AND 99)
);

ALTER TABLE equipo
    ADD CONSTRAINT fk_equipo_capitan FOREIGN KEY (id_equipo, ci_capitan)
        REFERENCES equipo_jugador_torneo (id_equipo, ci_jugador);

CREATE TABLE complejo (
    id_complejo  INT AUTO_INCREMENT,
    nombre       VARCHAR(80)  NOT NULL,
    direccion    VARCHAR(150) NOT NULL,
    departamento ENUM('Artigas', 'Canelones', 'Cerro Largo', 'Colonia', 'Durazno', 'Flores',
                      'Florida', 'Lavalleja', 'Maldonado', 'Montevideo', 'Paysandú', 'Río Negro',
                      'Rivera', 'Rocha', 'Salto', 'San José', 'Soriano', 'Tacuarembó',
                      'Treinta y Tres') NOT NULL,
    CONSTRAINT pk_complejo PRIMARY KEY (id_complejo),
    CONSTRAINT uq_complejo_nombre UNIQUE (nombre),
    CONSTRAINT chk_complejo_nombre    CHECK (CHAR_LENGTH(TRIM(nombre)) >= 3),
    CONSTRAINT chk_complejo_direccion CHECK (CHAR_LENGTH(TRIM(direccion)) >= 5)
);

-- Una cancha se identifica por su nombre dentro del complejo.
CREATE TABLE cancha (
    id_complejo   INT         NOT NULL,
    nombre_cancha VARCHAR(40) NOT NULL,
    superficie    ENUM('sintetico', 'parquet') NOT NULL,
    techada       BOOLEAN     NOT NULL,
    CONSTRAINT pk_cancha PRIMARY KEY (id_complejo, nombre_cancha),
    CONSTRAINT fk_cancha_complejo FOREIGN KEY (id_complejo) REFERENCES complejo (id_complejo) ON DELETE CASCADE,
    CONSTRAINT chk_cancha_nombre CHECK (CHAR_LENGTH(TRIM(nombre_cancha)) >= 1)
);

-- Turnos de una hora entre las 18:00 y las 23:00.
CREATE TABLE turno (
    id_turno    TINYINT NOT NULL,
    hora_inicio TIME    NOT NULL,
    hora_fin    TIME    NOT NULL,
    CONSTRAINT pk_turno PRIMARY KEY (id_turno),
    CONSTRAINT uq_turno_inicio UNIQUE (hora_inicio),
    CONSTRAINT chk_turno_rango    CHECK (hora_inicio >= '18:00:00' AND hora_fin <= '23:00:00'),
    CONSTRAINT chk_turno_hora     CHECK (hora_fin = ADDTIME(hora_inicio, '01:00:00')),
    CONSTRAINT chk_turno_en_punto CHECK (MINUTE(hora_inicio) = 0 AND SECOND(hora_inicio) = 0)
);

-- Columnas generadas: permiten expresar con UNIQUE reglas "condicionales".
--  * (torneo, equipo_menor, equipo_mayor, vigente): dos equipos no pueden
--    tener más de un partido no cancelado en la edición (vigente es NULL
--    cuando el partido está cancelado, y los NULL no chocan en un UNIQUE).
--  * (complejo, cancha, dia, turno, ocupa_cancha): una cancha no puede
--    tener dos partidos programados/jugados en el mismo día y turno.
CREATE TABLE partido (
    id_partido          INT AUTO_INCREMENT,
    id_torneo           INT              NOT NULL,
    numero_fecha        TINYINT UNSIGNED NOT NULL,
    id_equipo_local     INT              NOT NULL,
    id_equipo_visitante INT              NOT NULL,
    dia                 DATE             NOT NULL,
    id_turno            TINYINT          NOT NULL,
    id_complejo         INT              NOT NULL,
    nombre_cancha       VARCHAR(40)      NOT NULL,
    estado              ENUM('programado', 'jugado', 'postergado', 'cancelado') NOT NULL DEFAULT 'programado',
    equipo_menor        INT     AS (LEAST(id_equipo_local, id_equipo_visitante)) STORED,
    equipo_mayor        INT     AS (GREATEST(id_equipo_local, id_equipo_visitante)) STORED,
    vigente             TINYINT AS (IF(estado <> 'cancelado', 1, NULL)) STORED,
    ocupa_cancha        TINYINT AS (IF(estado IN ('programado', 'jugado'), 1, NULL)) STORED,
    CONSTRAINT pk_partido PRIMARY KEY (id_partido),
    CONSTRAINT fk_partido_torneo    FOREIGN KEY (id_torneo) REFERENCES torneo (id_torneo),
    CONSTRAINT fk_partido_local     FOREIGN KEY (id_equipo_local, id_torneo)     REFERENCES equipo (id_equipo, id_torneo),
    CONSTRAINT fk_partido_visitante FOREIGN KEY (id_equipo_visitante, id_torneo) REFERENCES equipo (id_equipo, id_torneo),
    CONSTRAINT fk_partido_turno     FOREIGN KEY (id_turno) REFERENCES turno (id_turno),
    CONSTRAINT fk_partido_cancha    FOREIGN KEY (id_complejo, nombre_cancha)
        REFERENCES cancha (id_complejo, nombre_cancha) ON UPDATE CASCADE,
    CONSTRAINT chk_partido_rivales CHECK (id_equipo_local <> id_equipo_visitante),
    CONSTRAINT chk_partido_fecha   CHECK (numero_fecha BETWEEN 1 AND 50),
    CONSTRAINT uq_partido_cruce  UNIQUE (id_torneo, equipo_menor, equipo_mayor, vigente),
    CONSTRAINT uq_partido_cancha UNIQUE (id_complejo, nombre_cancha, dia, id_turno, ocupa_cancha)
);

-- La FK compuesta contra el plantel garantiza que el jugador pertenece
-- al equipo indicado.
CREATE TABLE planilla_partido (
    id_partido INT        NOT NULL,
    ci_jugador VARCHAR(8) NOT NULL,
    id_equipo  INT        NOT NULL,
    CONSTRAINT pk_planilla PRIMARY KEY (id_partido, ci_jugador),
    CONSTRAINT fk_planilla_partido FOREIGN KEY (id_partido) REFERENCES partido (id_partido) ON DELETE CASCADE,
    CONSTRAINT fk_planilla_plantel FOREIGN KEY (id_equipo, ci_jugador)
        REFERENCES equipo_jugador_torneo (id_equipo, ci_jugador)
);

-- Solo pueden convertir jugadores que figuran en la planilla (FK compuesta).
CREATE TABLE gol (
    id_gol     INT AUTO_INCREMENT,
    id_partido INT              NOT NULL,
    ci_jugador VARCHAR(8)       NOT NULL,
    minuto     TINYINT UNSIGNED NOT NULL,
    autogol    BOOLEAN          NOT NULL DEFAULT FALSE,
    CONSTRAINT pk_gol PRIMARY KEY (id_gol),
    CONSTRAINT fk_gol_planilla FOREIGN KEY (id_partido, ci_jugador)
        REFERENCES planilla_partido (id_partido, ci_jugador) ON DELETE CASCADE,
    CONSTRAINT chk_gol_minuto CHECK (minuto BETWEEN 1 AND 60)
);

CREATE TABLE tarjeta (
    id_tarjeta INT AUTO_INCREMENT,
    id_partido INT              NOT NULL,
    ci_jugador VARCHAR(8)       NOT NULL,
    minuto     TINYINT UNSIGNED NOT NULL,
    color      ENUM('amarilla', 'roja') NOT NULL,
    CONSTRAINT pk_tarjeta PRIMARY KEY (id_tarjeta),
    CONSTRAINT fk_tarjeta_planilla FOREIGN KEY (id_partido, ci_jugador)
        REFERENCES planilla_partido (id_partido, ci_jugador) ON DELETE CASCADE,
    CONSTRAINT chk_tarjeta_minuto CHECK (minuto BETWEEN 1 AND 60)
);

-- Sanciones. Las automáticas (roja / acumulación de amarillas) quedan
-- vinculadas a la tarjeta que las originó: si la tarjeta se elimina al
-- corregir una planilla, la sanción desaparece en cascada.
CREATE TABLE sancion_jugador (
    id_sancion          INT AUTO_INCREMENT,
    ci_jugador          VARCHAR(8)       NOT NULL,
    id_torneo           INT              NOT NULL,
    motivo              ENUM('roja', 'acumulacion_amarillas', 'disciplinaria') NOT NULL,
    numero_fecha_inicio TINYINT UNSIGNED NOT NULL,
    cantidad_fechas     TINYINT UNSIGNED NOT NULL DEFAULT 1,
    id_tarjeta          INT              NULL,
    observaciones       VARCHAR(255)     NULL,
    fecha_registro      DATETIME         NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_sancion PRIMARY KEY (id_sancion),
    CONSTRAINT uq_sancion_tarjeta UNIQUE (id_tarjeta),
    CONSTRAINT fk_sancion_plantel FOREIGN KEY (ci_jugador, id_torneo)
        REFERENCES equipo_jugador_torneo (ci_jugador, id_torneo),
    CONSTRAINT fk_sancion_tarjeta FOREIGN KEY (id_tarjeta) REFERENCES tarjeta (id_tarjeta) ON DELETE CASCADE,
    CONSTRAINT chk_sancion_cantidad CHECK (cantidad_fechas BETWEEN 1 AND 20),
    CONSTRAINT chk_sancion_fecha    CHECK (numero_fecha_inicio BETWEEN 1 AND 51),
    CONSTRAINT chk_sancion_origen   CHECK ((motivo = 'disciplinaria') = (id_tarjeta IS NULL))
);

-- Índices de apoyo para los controles y reportes más frecuentes.
CREATE INDEX ix_partido_torneo_fecha ON partido (id_torneo, numero_fecha);
CREATE INDEX ix_sancion_jugador ON sancion_jugador (ci_jugador, id_torneo);

-- ---------------------------------------------------------------------
--  FUNCIONES Y PROCEDIMIENTOS
-- ---------------------------------------------------------------------
DELIMITER //

-- Valida el dígito verificador de una cédula uruguaya (pesos 2987634).
CREATE FUNCTION fn_ci_valida(p_ci VARCHAR(8)) RETURNS BOOLEAN
DETERMINISTIC NO SQL
BEGIN
    DECLARE v_ci    CHAR(8);
    DECLARE v_suma  INT DEFAULT 0;
    DECLARE v_i     INT DEFAULT 1;
    DECLARE v_pesos CHAR(7) DEFAULT '2987634';
    IF p_ci IS NULL OR p_ci NOT REGEXP '^[0-9]{7,8}$' THEN
        RETURN FALSE;
    END IF;
    SET v_ci = LPAD(p_ci, 8, '0');
    WHILE v_i <= 7 DO
        SET v_suma = v_suma + CAST(SUBSTRING(v_ci, v_i, 1) AS UNSIGNED)
                            * CAST(SUBSTRING(v_pesos, v_i, 1) AS UNSIGNED);
        SET v_i = v_i + 1;
    END WHILE;
    RETURN MOD(10 - MOD(v_suma, 10), 10) = CAST(SUBSTRING(v_ci, 8, 1) AS UNSIGNED);
END//

-- ¿El jugador está suspendido para esa fecha del torneo?
CREATE FUNCTION fn_jugador_suspendido(p_ci VARCHAR(8), p_torneo INT, p_fecha INT) RETURNS BOOLEAN
READS SQL DATA
BEGIN
    RETURN EXISTS (
        SELECT 1
          FROM sancion_jugador s
         WHERE s.ci_jugador = p_ci
           AND s.id_torneo = p_torneo
           AND p_fecha BETWEEN s.numero_fecha_inicio
                           AND s.numero_fecha_inicio + s.cantidad_fechas - 1
    );
END//

CREATE FUNCTION fn_tamano_plantel(p_equipo INT) RETURNS INT
READS SQL DATA
BEGIN
    RETURN (SELECT COUNT(*) FROM equipo_jugador_torneo WHERE id_equipo = p_equipo);
END//

-- Controla que el torneo esté en etapa de inscripción (planteles/equipos).
CREATE PROCEDURE sp_exigir_inscripcion(IN p_torneo INT)
BEGIN
    IF (SELECT estado FROM torneo WHERE id_torneo = p_torneo) <> 'inscripcion' THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Los equipos y planteles solo pueden modificarse con el torneo en etapa de inscripción.';
    END IF;
END//

-- Reglas al programar o modificar un partido.
CREATE PROCEDURE sp_validar_partido(
    IN p_id_partido INT, IN p_torneo INT, IN p_fecha INT,
    IN p_local INT, IN p_visitante INT, IN p_dia DATE,
    IN p_turno INT, IN p_complejo INT, IN p_cancha VARCHAR(40), IN p_estado VARCHAR(20))
BEGIN
    DECLARE v_estado_torneo VARCHAR(20);
    DECLARE v_inicio DATE;
    DECLARE v_fin DATE;
    DECLARE v_msg VARCHAR(128);
    DECLARE v_equipo INT;

    SELECT estado, fecha_inicio, fecha_fin INTO v_estado_torneo, v_inicio, v_fin
      FROM torneo WHERE id_torneo = p_torneo;

    IF v_estado_torneo = 'finalizado' THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'No se pueden programar ni modificar partidos de un torneo finalizado.';
    END IF;

    IF p_dia NOT BETWEEN v_inicio AND v_fin THEN
        SET v_msg = CONCAT('El día del partido debe estar entre ', DATE_FORMAT(v_inicio, '%d/%m/%Y'),
                           ' y ', DATE_FORMAT(v_fin, '%d/%m/%Y'), '.');
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = v_msg;
    END IF;

    IF p_local = p_visitante THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Un equipo no puede enfrentarse a sí mismo.';
    END IF;

    IF fn_tamano_plantel(p_local) < 5 OR fn_tamano_plantel(p_visitante) < 5 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Ambos equipos deben tener al menos 5 jugadores en su plantel.';
    END IF;

    IF EXISTS (SELECT 1 FROM partido
                WHERE id_torneo = p_torneo AND id_partido <> p_id_partido AND estado <> 'cancelado'
                  AND equipo_menor = LEAST(p_local, p_visitante)
                  AND equipo_mayor = GREATEST(p_local, p_visitante)) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Estos equipos ya tienen un partido (no cancelado) en esta edición.';
    END IF;

    SELECT e.id_equipo INTO v_equipo
      FROM partido p
      JOIN equipo e ON e.id_equipo IN (p.id_equipo_local, p.id_equipo_visitante)
     WHERE p.id_torneo = p_torneo AND p.numero_fecha = p_fecha
       AND p.id_partido <> p_id_partido AND p.estado <> 'cancelado'
       AND e.id_equipo IN (p_local, p_visitante)
     LIMIT 1;
    IF v_equipo IS NOT NULL THEN
        SET v_msg = CONCAT('El equipo "', (SELECT nombre FROM equipo WHERE id_equipo = v_equipo),
                           '" ya juega otro partido en la fecha ', p_fecha, '.');
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = v_msg;
    END IF;

    IF p_estado IN ('programado', 'jugado') AND EXISTS (
        SELECT 1 FROM partido
         WHERE id_complejo = p_complejo AND nombre_cancha = p_cancha
           AND dia = p_dia AND id_turno = p_turno
           AND estado IN ('programado', 'jugado') AND id_partido <> p_id_partido) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'La cancha ya tiene un partido asignado en ese día y turno.';
    END IF;
END//

-- Ventana en la que se puede registrar/corregir la planilla de un partido.
CREATE PROCEDURE sp_validar_ventana_planilla(IN p_id_partido INT)
BEGIN
    DECLARE v_estado VARCHAR(20);
    DECLARE v_inicio DATETIME;
    DECLARE v_fin DATETIME;

    SELECT p.estado, TIMESTAMP(p.dia, t.hora_inicio), TIMESTAMP(p.dia, t.hora_fin)
      INTO v_estado, v_inicio, v_fin
      FROM partido p JOIN turno t ON t.id_turno = p.id_turno
     WHERE p.id_partido = p_id_partido;

    IF v_estado IN ('cancelado', 'postergado') THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'No se puede registrar la planilla de un partido cancelado o postergado.';
    END IF;
    IF v_inicio > NOW() THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'La planilla solo puede registrarse una vez que el partido comenzó.';
    END IF;
    IF v_estado = 'jugado' AND NOW() > v_fin + INTERVAL 48 HOUR THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'El resultado solo puede corregirse dentro de las 48 horas posteriores al partido.';
    END IF;
END//

-- Recalcula las sanciones por acumulación de amarillas de un jugador en
-- una edición: cada 3 amarillas (3, 6, 9...) corresponde 1 fecha de
-- suspensión en la fecha siguiente a la de la tarjeta que completó el ciclo.
CREATE PROCEDURE sp_recalcular_amarillas(IN p_ci VARCHAR(8), IN p_torneo INT)
BEGIN
    DELETE FROM sancion_jugador
     WHERE ci_jugador = p_ci AND id_torneo = p_torneo AND motivo = 'acumulacion_amarillas';

    INSERT INTO sancion_jugador (ci_jugador, id_torneo, motivo, numero_fecha_inicio,
                                 cantidad_fechas, id_tarjeta, observaciones)
    SELECT p_ci, p_torneo, 'acumulacion_amarillas', x.numero_fecha + 1, 1, x.id_tarjeta,
           CONCAT('Automática: ', x.rn, ' amarillas acumuladas (fecha ', x.numero_fecha, ')')
      FROM (SELECT t.id_tarjeta, p.numero_fecha,
                   ROW_NUMBER() OVER (ORDER BY p.numero_fecha, p.dia, t.minuto, t.id_tarjeta) AS rn
              FROM tarjeta t
              JOIN partido p ON p.id_partido = t.id_partido
             WHERE t.ci_jugador = p_ci AND p.id_torneo = p_torneo AND t.color = 'amarilla') x
     WHERE MOD(x.rn, 3) = 0;
END//

-- ---------------------------------------------------------------------
--  TRIGGERS
-- ---------------------------------------------------------------------

-- JUGADOR ---------------------------------------------------------------
CREATE TRIGGER trg_jugador_bi BEFORE INSERT ON jugador FOR EACH ROW
BEGIN
    IF NOT fn_ci_valida(NEW.ci) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'La cédula ingresada no es válida (dígito verificador incorrecto).';
    END IF;
    IF TIMESTAMPDIFF(YEAR, NEW.fecha_nacimiento, CURDATE()) NOT BETWEEN 16 AND 100 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'El jugador debe tener entre 16 y 100 años.';
    END IF;
END//

CREATE TRIGGER trg_jugador_bu BEFORE UPDATE ON jugador FOR EACH ROW
BEGIN
    IF NEW.ci <> OLD.ci THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'La cédula de un jugador no puede modificarse.';
    END IF;
    IF TIMESTAMPDIFF(YEAR, NEW.fecha_nacimiento, CURDATE()) NOT BETWEEN 16 AND 100 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'El jugador debe tener entre 16 y 100 años.';
    END IF;
    IF NEW.id_facultad <> OLD.id_facultad AND EXISTS (
        SELECT 1 FROM equipo_jugador_torneo ejt
          JOIN torneo t ON t.id_torneo = ejt.id_torneo
         WHERE ejt.ci_jugador = NEW.ci AND t.estado <> 'finalizado') THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'No se puede cambiar la facultad de un jugador que integra un plantel en un torneo activo.';
    END IF;
    IF NEW.tipo IN ('docente', 'funcionario') AND OLD.tipo NOT IN ('docente', 'funcionario') AND EXISTS (
        SELECT 1 FROM equipo_jugador_torneo mio
          JOIN torneo t ON t.id_torneo = mio.id_torneo AND t.estado <> 'finalizado'
         WHERE mio.ci_jugador = NEW.ci
           AND (SELECT COUNT(*) FROM equipo_jugador_torneo o
                  JOIN jugador j ON j.ci = o.ci_jugador
                 WHERE o.id_equipo = mio.id_equipo AND j.tipo IN ('docente', 'funcionario')) >= 2) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'El cambio de tipo dejaría a su equipo con más de 2 docentes/funcionarios.';
    END IF;
END//

-- TORNEO ----------------------------------------------------------------
CREATE TRIGGER trg_torneo_bi BEFORE INSERT ON torneo FOR EACH ROW
BEGIN
    IF NEW.estado <> 'inscripcion' THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Un torneo nuevo debe comenzar en etapa de inscripción.';
    END IF;
END//

CREATE TRIGGER trg_torneo_bu BEFORE UPDATE ON torneo FOR EACH ROW
BEGIN
    DECLARE v_msg VARCHAR(128);
    IF NEW.estado <> OLD.estado THEN
        IF NOT ((OLD.estado = 'inscripcion' AND NEW.estado = 'en_curso')
             OR (OLD.estado = 'en_curso' AND NEW.estado = 'finalizado')) THEN
            SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Transición de estado inválida: inscripción -> en curso -> finalizado.';
        END IF;
        IF NEW.estado = 'en_curso' THEN
            IF (SELECT COUNT(*) FROM equipo WHERE id_torneo = NEW.id_torneo) < 2 THEN
                SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'El torneo necesita al menos 2 equipos para comenzar.';
            END IF;
            SELECT CONCAT('El equipo "', e.nombre, '" debe tener entre 5 y 10 jugadores y un capitán asignado.')
              INTO v_msg
              FROM equipo e
             WHERE e.id_torneo = NEW.id_torneo
               AND (e.ci_capitan IS NULL OR fn_tamano_plantel(e.id_equipo) NOT BETWEEN 5 AND 10)
             LIMIT 1;
            IF v_msg IS NOT NULL THEN
                SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = v_msg;
            END IF;
        END IF;
        IF NEW.estado = 'finalizado' AND EXISTS (
            SELECT 1 FROM partido WHERE id_torneo = NEW.id_torneo AND estado IN ('programado', 'postergado')) THEN
            SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'No se puede finalizar: hay partidos programados o postergados pendientes.';
        END IF;
    END IF;
    IF (NEW.fecha_inicio <> OLD.fecha_inicio OR NEW.fecha_fin <> OLD.fecha_fin) AND EXISTS (
        SELECT 1 FROM partido WHERE id_torneo = NEW.id_torneo
           AND dia NOT BETWEEN NEW.fecha_inicio AND NEW.fecha_fin) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Hay partidos programados fuera del nuevo rango de fechas del torneo.';
    END IF;
END//

-- EQUIPO ----------------------------------------------------------------
CREATE TRIGGER trg_equipo_bi BEFORE INSERT ON equipo FOR EACH ROW
BEGIN
    CALL sp_exigir_inscripcion(NEW.id_torneo);
    IF NEW.ci_capitan IS NOT NULL THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'El capitán se asigna después de cargar el plantel del equipo.';
    END IF;
END//

CREATE TRIGGER trg_equipo_bu BEFORE UPDATE ON equipo FOR EACH ROW
BEGIN
    IF NEW.id_torneo <> OLD.id_torneo THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Un equipo no puede cambiar de edición del torneo.';
    END IF;
    IF NEW.id_facultad <> OLD.id_facultad AND fn_tamano_plantel(OLD.id_equipo) > 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'No se puede cambiar la facultad de un equipo que ya tiene jugadores.';
    END IF;
    IF NOT (NEW.ci_capitan <=> OLD.ci_capitan) AND NEW.ci_capitan IS NULL
       AND (SELECT estado FROM torneo WHERE id_torneo = NEW.id_torneo) <> 'inscripcion' THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Con el torneo en curso el equipo debe tener un capitán.';
    END IF;
END//

CREATE TRIGGER trg_equipo_bd BEFORE DELETE ON equipo FOR EACH ROW
BEGIN
    CALL sp_exigir_inscripcion(OLD.id_torneo);
END//

-- PLANTEL ---------------------------------------------------------------
CREATE TRIGGER trg_plantel_bi BEFORE INSERT ON equipo_jugador_torneo FOR EACH ROW
BEGIN
    DECLARE v_tipo VARCHAR(20);
    DECLARE v_fac_jugador INT;
    CALL sp_exigir_inscripcion(NEW.id_torneo);

    SELECT tipo, id_facultad INTO v_tipo, v_fac_jugador FROM jugador WHERE ci = NEW.ci_jugador;
    IF v_fac_jugador <> (SELECT id_facultad FROM equipo WHERE id_equipo = NEW.id_equipo) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'El jugador debe pertenecer a la facultad que representa el equipo.';
    END IF;
    IF fn_tamano_plantel(NEW.id_equipo) >= 10 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'El plantel ya tiene 10 jugadores (máximo permitido).';
    END IF;
    IF v_tipo IN ('docente', 'funcionario') AND (
        SELECT COUNT(*) FROM equipo_jugador_torneo ejt JOIN jugador j ON j.ci = ejt.ci_jugador
         WHERE ejt.id_equipo = NEW.id_equipo AND j.tipo IN ('docente', 'funcionario')) >= 2 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'El plantel ya tiene 2 docentes/funcionarios (máximo permitido).';
    END IF;
END//

CREATE TRIGGER trg_plantel_bu BEFORE UPDATE ON equipo_jugador_torneo FOR EACH ROW
BEGIN
    CALL sp_exigir_inscripcion(OLD.id_torneo);
    IF NEW.id_equipo <> OLD.id_equipo OR NEW.ci_jugador <> OLD.ci_jugador OR NEW.id_torneo <> OLD.id_torneo THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Para cambiar un jugador de equipo, quítelo del plantel y vuelva a agregarlo.';
    END IF;
END//

CREATE TRIGGER trg_plantel_bd BEFORE DELETE ON equipo_jugador_torneo FOR EACH ROW
BEGIN
    CALL sp_exigir_inscripcion(OLD.id_torneo);
    IF EXISTS (SELECT 1 FROM equipo WHERE id_equipo = OLD.id_equipo AND ci_capitan = OLD.ci_jugador) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'El jugador es el capitán: asigne otro capitán antes de quitarlo del plantel.';
    END IF;
END//

-- PARTIDO ---------------------------------------------------------------
CREATE TRIGGER trg_partido_bi BEFORE INSERT ON partido FOR EACH ROW
BEGIN
    IF NEW.estado <> 'programado' THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Un partido nuevo debe crearse en estado programado.';
    END IF;
    CALL sp_validar_partido(0, NEW.id_torneo, NEW.numero_fecha, NEW.id_equipo_local, NEW.id_equipo_visitante,
                            NEW.dia, NEW.id_turno, NEW.id_complejo, NEW.nombre_cancha, NEW.estado);
END//

CREATE TRIGGER trg_partido_bu BEFORE UPDATE ON partido FOR EACH ROW
BEGIN
    DECLARE v_cambia_datos BOOLEAN;
    DECLARE v_tiene_planilla BOOLEAN;
    SET v_cambia_datos = NOT (NEW.id_torneo <=> OLD.id_torneo AND NEW.numero_fecha <=> OLD.numero_fecha
        AND NEW.id_equipo_local <=> OLD.id_equipo_local AND NEW.id_equipo_visitante <=> OLD.id_equipo_visitante
        AND NEW.dia <=> OLD.dia AND NEW.id_turno <=> OLD.id_turno
        AND NEW.id_complejo <=> OLD.id_complejo AND NEW.nombre_cancha <=> OLD.nombre_cancha);
    SET v_tiene_planilla = EXISTS (SELECT 1 FROM planilla_partido WHERE id_partido = OLD.id_partido);

    -- Los planilleros solo pueden marcar como jugado un partido programado.
    IF SUBSTRING_INDEX(USER(), '@', 1) = 'tf5_planillero'
       AND NOT (OLD.estado = 'programado' AND NEW.estado = 'jugado' AND NOT v_cambia_datos) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Un planillero solo puede marcar como jugado un partido programado.';
    END IF;

    IF OLD.estado = 'jugado' AND (v_cambia_datos OR NEW.estado <> 'jugado') THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Un partido jugado no puede modificarse (solo corregir su planilla dentro de 48 h).';
    END IF;
    IF OLD.estado = 'cancelado' AND (v_cambia_datos OR NEW.estado <> 'cancelado') THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Un partido cancelado no puede modificarse.';
    END IF;

    IF v_tiene_planilla AND (v_cambia_datos OR NEW.estado IN ('postergado', 'cancelado')) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'El partido ya tiene planilla cargada: no puede reprogramarse, postergarse ni cancelarse.';
    END IF;

    IF NEW.estado = 'jugado' AND OLD.estado <> 'jugado' THEN
        IF OLD.estado <> 'programado' THEN
            SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Solo un partido programado puede marcarse como jugado.';
        END IF;
        IF TIMESTAMP(NEW.dia, (SELECT hora_fin FROM turno WHERE id_turno = NEW.id_turno)) > NOW() THEN
            SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Un partido solo puede marcarse como jugado cuando su día y turno ya pasaron.';
        END IF;
        IF NOT EXISTS (SELECT 1 FROM planilla_partido WHERE id_partido = NEW.id_partido AND id_equipo = NEW.id_equipo_local)
           OR NOT EXISTS (SELECT 1 FROM planilla_partido WHERE id_partido = NEW.id_partido AND id_equipo = NEW.id_equipo_visitante) THEN
            SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Antes de marcarlo como jugado, la planilla debe tener jugadores de ambos equipos.';
        END IF;
    END IF;

    IF NEW.estado <> 'cancelado' AND (v_cambia_datos OR NEW.estado <> OLD.estado) THEN
        CALL sp_validar_partido(OLD.id_partido, NEW.id_torneo, NEW.numero_fecha, NEW.id_equipo_local,
                                NEW.id_equipo_visitante, NEW.dia, NEW.id_turno, NEW.id_complejo,
                                NEW.nombre_cancha, NEW.estado);
    END IF;
END//

CREATE TRIGGER trg_partido_bd BEFORE DELETE ON partido FOR EACH ROW
BEGIN
    IF OLD.estado = 'jugado' THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Un partido jugado no puede eliminarse.';
    END IF;
    IF EXISTS (SELECT 1 FROM planilla_partido WHERE id_partido = OLD.id_partido) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'El partido tiene planilla cargada: elimine primero la planilla.';
    END IF;
END//

-- PLANILLA --------------------------------------------------------------
CREATE TRIGGER trg_planilla_bi BEFORE INSERT ON planilla_partido FOR EACH ROW
BEGIN
    DECLARE v_torneo INT;
    DECLARE v_fecha INT;
    DECLARE v_local INT;
    DECLARE v_visitante INT;
    DECLARE v_msg VARCHAR(128);

    CALL sp_validar_ventana_planilla(NEW.id_partido);

    SELECT id_torneo, numero_fecha, id_equipo_local, id_equipo_visitante
      INTO v_torneo, v_fecha, v_local, v_visitante
      FROM partido WHERE id_partido = NEW.id_partido;

    IF NEW.id_equipo NOT IN (v_local, v_visitante) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'El jugador debe pertenecer a uno de los dos equipos del partido.';
    END IF;
    IF fn_jugador_suspendido(NEW.ci_jugador, v_torneo, v_fecha) THEN
        SET v_msg = CONCAT('El jugador ', NEW.ci_jugador, ' está suspendido para la fecha ', v_fecha, '.');
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = v_msg;
    END IF;
END//

CREATE TRIGGER trg_planilla_bu BEFORE UPDATE ON planilla_partido FOR EACH ROW
BEGIN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'La planilla no se modifica: quite el jugador y vuelva a agregarlo.';
END//

CREATE TRIGGER trg_planilla_bd BEFORE DELETE ON planilla_partido FOR EACH ROW
BEGIN
    CALL sp_validar_ventana_planilla(OLD.id_partido);
    IF EXISTS (SELECT 1 FROM gol WHERE id_partido = OLD.id_partido AND ci_jugador = OLD.ci_jugador)
       OR EXISTS (SELECT 1 FROM tarjeta WHERE id_partido = OLD.id_partido AND ci_jugador = OLD.ci_jugador) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'El jugador tiene goles o tarjetas en el partido: elimínelos antes de quitarlo de la planilla.';
    END IF;
END//

-- GOL -------------------------------------------------------------------
CREATE TRIGGER trg_gol_bi BEFORE INSERT ON gol FOR EACH ROW
BEGIN
    CALL sp_validar_ventana_planilla(NEW.id_partido);
END//

CREATE TRIGGER trg_gol_bu BEFORE UPDATE ON gol FOR EACH ROW
BEGIN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Para corregir un gol, elimínelo y vuelva a registrarlo.';
END//

CREATE TRIGGER trg_gol_bd BEFORE DELETE ON gol FOR EACH ROW
BEGIN
    CALL sp_validar_ventana_planilla(OLD.id_partido);
END//

-- TARJETA ---------------------------------------------------------------
CREATE TRIGGER trg_tarjeta_bi BEFORE INSERT ON tarjeta FOR EACH ROW
BEGIN
    CALL sp_validar_ventana_planilla(NEW.id_partido);
    IF EXISTS (SELECT 1 FROM tarjeta WHERE id_partido = NEW.id_partido AND ci_jugador = NEW.ci_jugador AND color = 'roja') THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'El jugador ya fue expulsado (roja) en este partido.';
    END IF;
    IF NEW.color = 'amarilla' AND (SELECT COUNT(*) FROM tarjeta WHERE id_partido = NEW.id_partido
                                     AND ci_jugador = NEW.ci_jugador AND color = 'amarilla') >= 2 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Un jugador no puede recibir más de 2 amarillas en un partido.';
    END IF;
END//

CREATE TRIGGER trg_tarjeta_ai AFTER INSERT ON tarjeta FOR EACH ROW
BEGIN
    DECLARE v_torneo INT;
    DECLARE v_fecha INT;
    SELECT id_torneo, numero_fecha INTO v_torneo, v_fecha FROM partido WHERE id_partido = NEW.id_partido;
    IF NEW.color = 'roja' THEN
        INSERT INTO sancion_jugador (ci_jugador, id_torneo, motivo, numero_fecha_inicio, cantidad_fechas,
                                     id_tarjeta, observaciones)
        VALUES (NEW.ci_jugador, v_torneo, 'roja', v_fecha + 1, 1, NEW.id_tarjeta,
                CONCAT('Automática: tarjeta roja en la fecha ', v_fecha));
    ELSE
        CALL sp_recalcular_amarillas(NEW.ci_jugador, v_torneo);
    END IF;
END//

CREATE TRIGGER trg_tarjeta_bu BEFORE UPDATE ON tarjeta FOR EACH ROW
BEGIN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Para corregir una tarjeta, elimínela y vuelva a registrarla.';
END//

CREATE TRIGGER trg_tarjeta_bd BEFORE DELETE ON tarjeta FOR EACH ROW
BEGIN
    CALL sp_validar_ventana_planilla(OLD.id_partido);
END//

CREATE TRIGGER trg_tarjeta_ad AFTER DELETE ON tarjeta FOR EACH ROW
BEGIN
    IF OLD.color = 'amarilla' THEN
        CALL sp_recalcular_amarillas(OLD.ci_jugador, (SELECT id_torneo FROM partido WHERE id_partido = OLD.id_partido));
    END IF;
END//

-- SANCIÓN ---------------------------------------------------------------
CREATE TRIGGER trg_sancion_bi BEFORE INSERT ON sancion_jugador FOR EACH ROW
BEGIN
    DECLARE v_fecha INT;
    IF NEW.motivo = 'disciplinaria' THEN
        SELECT MIN(p.numero_fecha) INTO v_fecha
          FROM planilla_partido pp JOIN partido p ON p.id_partido = pp.id_partido
         WHERE pp.ci_jugador = NEW.ci_jugador AND p.id_torneo = NEW.id_torneo
           AND p.numero_fecha BETWEEN NEW.numero_fecha_inicio AND NEW.numero_fecha_inicio + NEW.cantidad_fechas - 1;
        IF v_fecha IS NOT NULL THEN
            SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'El jugador ya figura en la planilla de una fecha que abarcaría la sanción.';
        END IF;
    END IF;
END//

CREATE TRIGGER trg_sancion_bu BEFORE UPDATE ON sancion_jugador FOR EACH ROW
BEGIN
    DECLARE v_fecha INT;
    IF OLD.motivo <> 'disciplinaria' OR NEW.motivo <> 'disciplinaria' THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Las sanciones automáticas no se editan: se corrigen desde la planilla del partido.';
    END IF;
    IF NEW.ci_jugador <> OLD.ci_jugador OR NEW.id_torneo <> OLD.id_torneo THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'No se puede cambiar el jugador ni el torneo de una sanción.';
    END IF;
    SELECT MIN(p.numero_fecha) INTO v_fecha
      FROM planilla_partido pp JOIN partido p ON p.id_partido = pp.id_partido
     WHERE pp.ci_jugador = NEW.ci_jugador AND p.id_torneo = NEW.id_torneo
       AND p.numero_fecha BETWEEN NEW.numero_fecha_inicio AND NEW.numero_fecha_inicio + NEW.cantidad_fechas - 1
       AND p.numero_fecha NOT BETWEEN OLD.numero_fecha_inicio AND OLD.numero_fecha_inicio + OLD.cantidad_fechas - 1;
    IF v_fecha IS NOT NULL THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'El jugador ya figura en la planilla de una fecha que abarcaría la sanción.';
    END IF;
END//

DELIMITER ;

-- ---------------------------------------------------------------------
--  VISTAS (base de los reportes)
-- ---------------------------------------------------------------------

-- Resultado de cada partido calculado a partir de los goles registrados.
-- Un autogol suma para el rival del equipo del jugador.
CREATE VIEW v_resultado_partido AS
SELECT p.id_partido, p.id_torneo, p.numero_fecha, p.dia, p.id_turno, p.id_complejo, p.nombre_cancha,
       p.estado, p.id_equipo_local, p.id_equipo_visitante,
       COALESCE(SUM(CASE WHEN (pp.id_equipo = p.id_equipo_local AND g.autogol = FALSE)
                           OR (pp.id_equipo = p.id_equipo_visitante AND g.autogol = TRUE) THEN 1 ELSE 0 END), 0) AS goles_local,
       COALESCE(SUM(CASE WHEN (pp.id_equipo = p.id_equipo_visitante AND g.autogol = FALSE)
                           OR (pp.id_equipo = p.id_equipo_local AND g.autogol = TRUE) THEN 1 ELSE 0 END), 0) AS goles_visitante
  FROM partido p
  LEFT JOIN gol g ON g.id_partido = p.id_partido
  LEFT JOIN planilla_partido pp ON pp.id_partido = g.id_partido AND pp.ci_jugador = g.ci_jugador
 GROUP BY p.id_partido;

-- Un renglón por equipo y partido jugado (goles a favor / en contra).
CREATE VIEW v_partido_equipo AS
SELECT id_partido, id_torneo, numero_fecha, id_equipo_local AS id_equipo, 'local' AS condicion,
       goles_local AS gf, goles_visitante AS gc
  FROM v_resultado_partido WHERE estado = 'jugado'
UNION ALL
SELECT id_partido, id_torneo, numero_fecha, id_equipo_visitante, 'visitante',
       goles_visitante, goles_local
  FROM v_resultado_partido WHERE estado = 'jugado';

CREATE VIEW v_tabla_posiciones AS
SELECT e.id_torneo, e.id_equipo, e.nombre AS equipo, f.nombre AS facultad,
       COUNT(pe.id_partido)                AS pj,
       COALESCE(SUM(pe.gf > pe.gc), 0)     AS pg,
       COALESCE(SUM(pe.gf = pe.gc), 0)     AS pe,
       COALESCE(SUM(pe.gf < pe.gc), 0)     AS pp,
       COALESCE(SUM(pe.gf), 0)             AS gf,
       COALESCE(SUM(pe.gc), 0)             AS gc,
       COALESCE(SUM(pe.gf) - SUM(pe.gc), 0) AS dg,
       COALESCE(3 * SUM(pe.gf > pe.gc) + SUM(pe.gf = pe.gc), 0) AS pts
  FROM equipo e
  JOIN facultad f ON f.id_facultad = e.id_facultad
  LEFT JOIN v_partido_equipo pe ON pe.id_equipo = e.id_equipo
 GROUP BY e.id_torneo, e.id_equipo, e.nombre, f.nombre;

-- Goles convertidos (sin autogoles) por jugador y edición.
CREATE VIEW v_goleadores AS
SELECT p.id_torneo, j.ci, j.nombre, j.apellido, e.id_equipo, e.nombre AS equipo,
       COUNT(*) AS goles, COUNT(DISTINCT g.id_partido) AS partidos_con_gol
  FROM gol g
  JOIN partido p           ON p.id_partido = g.id_partido AND p.estado = 'jugado'
  JOIN planilla_partido pp ON pp.id_partido = g.id_partido AND pp.ci_jugador = g.ci_jugador
  JOIN jugador j           ON j.ci = g.ci_jugador
  JOIN equipo e            ON e.id_equipo = pp.id_equipo
 WHERE g.autogol = FALSE
 GROUP BY p.id_torneo, j.ci, j.nombre, j.apellido, e.id_equipo, e.nombre;

-- Fair play: 1 punto por amarilla, 3 por roja (menor es mejor).
CREATE VIEW v_fair_play AS
SELECT e.id_torneo, e.id_equipo, e.nombre AS equipo,
       COALESCE(SUM(t.color = 'amarilla'), 0) AS amarillas,
       COALESCE(SUM(t.color = 'roja'), 0)     AS rojas,
       COALESCE(SUM(CASE t.color WHEN 'amarilla' THEN 1 WHEN 'roja' THEN 3 ELSE 0 END), 0) AS puntaje
  FROM equipo e
  LEFT JOIN planilla_partido pp ON pp.id_equipo = e.id_equipo
  LEFT JOIN tarjeta t ON t.id_partido = pp.id_partido AND t.ci_jugador = pp.ci_jugador
 GROUP BY e.id_torneo, e.id_equipo, e.nombre;

-- Sanciones con el equipo del jugador sancionado.
CREATE VIEW v_sancion_detalle AS
SELECT s.*, j.nombre, j.apellido, e.id_equipo, e.nombre AS equipo,
       s.numero_fecha_inicio + s.cantidad_fechas - 1 AS numero_fecha_fin
  FROM sancion_jugador s
  JOIN jugador j ON j.ci = s.ci_jugador
  JOIN equipo_jugador_torneo ejt ON ejt.ci_jugador = s.ci_jugador AND ejt.id_torneo = s.id_torneo
  JOIN equipo e ON e.id_equipo = ejt.id_equipo;
