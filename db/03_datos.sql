SET NAMES utf8mb4;
-- =====================================================================
--  Script 3/3: datos maestros y datos de prueba
--  Generado con herramientas/generar_datos.py
--  8 equipos, fechas 1 a 3 disputadas (una postergada), fecha 4 en curso
--  y fecha 5 programada. Las fechas de la fecha 4 y 5 se calculan respecto
--  a CURDATE() para que siempre haya un partido recién jugado (corregible
--  dentro de 48 h), uno pendiente de planilla y partidos futuros.
--  Las sanciones por roja/amarillas las generan los triggers.
-- =====================================================================
USE torneo_futbol5;

-- Usuarios de la aplicación (contraseñas: Admin123! / Planillero123!)
INSERT INTO login (correo, contrasena, rol) VALUES
    ('admin@ucu.edu.uy', 'pbkdf2:sha256:1000000$WqFaKCVvJMwu9Y6T$3a775364914370e69c991ae5b02dc7c690919a7dcce2c617814e0db6fb024914', 'administrador'),
    ('planillero@ucu.edu.uy', 'pbkdf2:sha256:1000000$dsw2a7EfUPcpJV1q$fe997ba5ad9c875e798eba1f612949d5084bfe7940e37db1d829c9b5eb5a29c0', 'planillero'),
    ('planillero2@ucu.edu.uy', 'pbkdf2:sha256:1000000$EkVAyNYDWxFZ8ziu$baee60d23a7fdceb21f05b556a14de83522cec3d8e6fd79fcbdd4451962f6319', 'planillero');

-- Datos maestros
INSERT INTO facultad (id_facultad, nombre) VALUES
    (1, 'Facultad de Ingeniería y Tecnologías'),
    (2, 'Facultad de Ciencias Empresariales'),
    (3, 'Facultad de Derecho'),
    (4, 'Facultad de Ciencias de la Salud'),
    (5, 'Facultad de Ciencias Humanas'),
    (6, 'Facultad de Psicología');
INSERT INTO turno (id_turno, hora_inicio, hora_fin) VALUES
    (1, '18:00:00', '19:00:00'),
    (2, '19:00:00', '20:00:00'),
    (3, '20:00:00', '21:00:00'),
    (4, '21:00:00', '22:00:00'),
    (5, '22:00:00', '23:00:00');
INSERT INTO complejo (id_complejo, nombre, direccion, departamento) VALUES
    (1, 'Complejo Pocitos Fútbol 5', 'Av. Brasil 2850', 'Montevideo'),
    (2, 'Arena Carrasco', 'Av. Italia 6201', 'Montevideo'),
    (3, 'Club Ciudad de la Costa', 'Av. Giannattasio km 21', 'Canelones');
INSERT INTO cancha (id_complejo, nombre_cancha, superficie, techada) VALUES
    (1, 'Cancha 1', 'sintetico', FALSE),
    (1, 'Cancha 2', 'sintetico', TRUE),
    (2, 'Central', 'parquet', TRUE),
    (2, 'Norte', 'sintetico', FALSE),
    (3, 'Cancha A', 'sintetico', FALSE);

-- Jugadores
INSERT INTO jugador (ci, nombre, apellido, email, fecha_nacimiento, id_facultad, tipo) VALUES
    ('41219379', 'Joaquín', 'Álvarez', 'joaquin.alvarez@correo.ucu.edu.uy', '1989-10-18', 1, 'docente'),
    ('41742762', 'Agustina', 'Machado', 'agustina.machado@correo.ucu.edu.uy', '1977-01-20', 1, 'funcionario'),
    ('41941007', 'Joaquín', 'Machado', 'joaquin.machado@correo.ucu.edu.uy', '1998-11-16', 1, 'posgrado'),
    ('42088771', 'Sofía', 'Acosta', 'sofia.acosta@correo.ucu.edu.uy', '2003-06-26', 1, 'grado'),
    ('42587642', 'Facundo', 'Correa', 'facundo.correa@correo.ucu.edu.uy', '1999-09-18', 1, 'grado'),
    ('42897431', 'Gonzalo', 'Ramírez', 'gonzalo.ramirez@correo.ucu.edu.uy', '1998-12-12', 1, 'grado'),
    ('43184132', 'Agustín', 'Morales', 'agustin.morales@correo.ucu.edu.uy', '2007-09-16', 1, 'grado'),
    ('43472949', 'Agustina', 'Morales', 'agustina.morales@correo.ucu.edu.uy', '2006-05-28', 1, 'grado'),
    ('43796981', 'Santiago', 'Álvarez', 'santiago.alvarez@correo.ucu.edu.uy', '2000-01-23', 1, 'grado'),
    ('44277071', 'Camila', 'Giménez', 'camila.gimenez@correo.ucu.edu.uy', '1974-08-08', 1, 'docente'),
    ('44367036', 'Carolina', 'Giménez', 'carolina.gimenez@correo.ucu.edu.uy', '2006-05-18', 1, 'grado'),
    ('44578639', 'Micaela', 'Morales', 'micaela.morales@correo.ucu.edu.uy', '2004-04-10', 1, 'grado'),
    ('44594708', 'Matías', 'Méndez', 'matias.mendez@correo.ucu.edu.uy', '2007-08-26', 1, 'grado'),
    ('44925511', 'Felipe', 'Castro', 'felipe.castro@correo.ucu.edu.uy', '2002-12-16', 1, 'grado'),
    ('45437977', 'Agustina', 'Ferreira', 'agustina.ferreira@correo.ucu.edu.uy', '2006-11-02', 1, 'grado'),
    ('45655496', 'Carolina', 'Sosa', 'carolina.sosa@correo.ucu.edu.uy', '2005-12-23', 1, 'grado'),
    ('45962318', 'Sebastián', 'Ferreira', 'sebastian.ferreira@correo.ucu.edu.uy', '1985-02-21', 2, 'funcionario'),
    ('46298954', 'Felipe', 'Sosa', 'felipe.sosa@correo.ucu.edu.uy', '2001-12-28', 2, 'grado'),
    ('46603466', 'Martín', 'Martínez', 'martin.martinez@correo.ucu.edu.uy', '1998-08-19', 2, 'grado'),
    ('47161570', 'Agustín', 'Castro', 'agustin.castro@correo.ucu.edu.uy', '2001-02-20', 2, 'grado'),
    ('47529697', 'Juan', 'Viera', 'juan.viera@correo.ucu.edu.uy', '2000-01-11', 2, 'posgrado'),
    ('47916054', 'Agustina', 'Díaz', 'agustina.diaz@correo.ucu.edu.uy', '2006-04-16', 2, 'grado'),
    ('48318045', 'Pablo', 'Martínez', 'pablo.martinez@correo.ucu.edu.uy', '2004-11-06', 2, 'grado'),
    ('48841472', 'Tomás', 'De León', 'tomas.deleon@correo.ucu.edu.uy', '2004-03-17', 2, 'grado'),
    ('49097880', 'Martín', 'Sosa', 'martin.sosa@correo.ucu.edu.uy', '2004-02-02', 2, 'grado'),
    ('49531424', 'Andrés', 'González', 'andres.gonzalez@correo.ucu.edu.uy', '1998-09-16', 2, 'grado'),
    ('49740433', 'Florencia', 'Techera', 'florencia.techera@correo.ucu.edu.uy', '1999-08-15', 2, 'grado'),
    ('50277956', 'Rodrigo', 'Méndez', 'rodrigo.mendez@correo.ucu.edu.uy', '2007-09-07', 2, 'grado'),
    ('50508422', 'Carolina', 'Álvarez', 'carolina.alvarez@correo.ucu.edu.uy', '1999-09-13', 2, 'grado'),
    ('50942581', 'Sebastián', 'Fernández', 'sebastian.fernandez@correo.ucu.edu.uy', '2006-01-15', 2, 'posgrado'),
    ('51372567', 'Lucas', 'Giménez', 'lucas.gimenez@correo.ucu.edu.uy', '1998-03-21', 2, 'grado'),
    ('51897284', 'Federico', 'Suárez', 'federico.suarez@correo.ucu.edu.uy', '1975-07-09', 3, 'docente'),
    ('52256594', 'Valentina', 'Martínez', 'valentina.martinez@correo.ucu.edu.uy', '1982-05-06', 3, 'funcionario'),
    ('52439243', 'Carolina', 'Da Silva', 'carolina.dasilva@correo.ucu.edu.uy', '2004-05-15', 3, 'grado'),
    ('52789595', 'Micaela', 'Machado', 'micaela.machado@correo.ucu.edu.uy', '1999-09-26', 3, 'grado'),
    ('52979041', 'Joaquín', 'Romero', 'joaquin.romero@correo.ucu.edu.uy', '2001-01-03', 3, 'grado'),
    ('53412193', 'Maximiliano', 'De León', 'maximiliano.deleon@correo.ucu.edu.uy', '2006-11-06', 3, 'grado'),
    ('53652848', 'Rodrigo', 'Viera', 'rodrigo.viera@correo.ucu.edu.uy', '2006-11-19', 3, 'grado'),
    ('53804754', 'Diego', 'Cabrera', 'diego.cabrera@correo.ucu.edu.uy', '2006-10-24', 3, 'grado'),
    ('54188193', 'Pablo', 'Cabrera', 'pablo.cabrera@correo.ucu.edu.uy', '1987-03-04', 4, 'docente'),
    ('54261389', 'Camila', 'Suárez', 'camila.suarez@correo.ucu.edu.uy', '1999-11-02', 4, 'grado'),
    ('54744783', 'Sebastián', 'Sosa', 'sebastian.sosa@correo.ucu.edu.uy', '2006-06-09', 4, 'grado'),
    ('54796667', 'Pablo', 'Techera', 'pablo.techera@correo.ucu.edu.uy', '2000-05-09', 4, 'grado'),
    ('55076436', 'Ignacio', 'De León', 'ignacio.deleon@correo.ucu.edu.uy', '1998-01-04', 4, 'posgrado'),
    ('55289532', 'Diego', 'Sosa', 'diego.sosa@correo.ucu.edu.uy', '2006-10-28', 4, 'grado'),
    ('55810559', 'Carolina', 'Fernández', 'carolina.fernandez@correo.ucu.edu.uy', '2004-06-20', 4, 'grado'),
    ('56123761', 'Camila', 'López', 'camila.lopez@correo.ucu.edu.uy', '2003-09-22', 5, 'grado'),
    ('56298639', 'Lucía', 'Olivera', 'lucia.olivera@correo.ucu.edu.uy', '2003-01-24', 5, 'grado'),
    ('56884303', 'Santiago', 'Olivera', 'santiago.olivera@correo.ucu.edu.uy', '2003-05-24', 5, 'grado'),
    ('57418486', 'Diego', 'Ramírez', 'diego.ramirez@correo.ucu.edu.uy', '2004-06-19', 5, 'grado'),
    ('57783784', 'Maximiliano', 'Castro', 'maximiliano.castro@correo.ucu.edu.uy', '2006-01-24', 5, 'grado'),
    ('57900027', 'Diego', 'López', 'diego.lopez@correo.ucu.edu.uy', '1998-03-17', 5, 'grado'),
    ('58301230', 'Tomás', 'González', 'tomas.gonzalez@correo.ucu.edu.uy', '1983-10-05', 6, 'funcionario'),
    ('58562957', 'Lucía', 'Benítez', 'lucia.benitez@correo.ucu.edu.uy', '2004-11-08', 6, 'grado'),
    ('58693184', 'Santiago', 'Morales', 'santiago.morales@correo.ucu.edu.uy', '2002-03-08', 6, 'grado'),
    ('58884606', 'Micaela', 'De León', 'micaela.deleon@correo.ucu.edu.uy', '2002-06-05', 6, 'posgrado'),
    ('59283651', 'Agustín', 'Núñez', 'agustin.nunez@correo.ucu.edu.uy', '2006-01-21', 6, 'grado'),
    ('59833523', 'Ignacio', 'Correa', 'ignacio.correa@correo.ucu.edu.uy', '2006-12-11', 6, 'grado'),
    ('60394449', 'Martín', 'Benítez', 'martin.benitez@correo.ucu.edu.uy', '2005-01-08', 6, 'posgrado'),
    ('60969436', 'Gonzalo', 'Morales', 'gonzalo.morales@correo.ucu.edu.uy', '2003-04-18', 6, 'grado'),
    ('61204667', 'Lucas', 'Píriz', 'lucas.piriz@correo.ucu.edu.uy', '2003-08-21', 1, 'posgrado'),
    ('61574313', 'Micaela', 'Ramírez', 'micaela.ramirez@correo.ucu.edu.uy', '1976-03-21', 1, 'docente'),
    ('61685099', 'Agustina', 'Rodríguez', 'agustina.rodriguez@correo.ucu.edu.uy', '1981-09-23', 2, 'docente'),
    ('62216346', 'Matías', 'Núñez', 'matias.nunez@correo.ucu.edu.uy', '1972-05-12', 2, 'docente'),
    ('62705418', 'Ignacio', 'Díaz', 'ignacio.diaz@correo.ucu.edu.uy', '1973-01-18', 3, 'funcionario'),
    ('63272349', 'Tomás', 'Fernández', 'tomas.fernandez@correo.ucu.edu.uy', '2004-07-18', 3, 'grado'),
    ('63814523', 'Rodrigo', 'Sosa', 'rodrigo.sosa@correo.ucu.edu.uy', '1972-03-24', 4, 'funcionario'),
    ('64043153', 'Ignacio', 'Ramírez', 'ignacio.ramirez@correo.ucu.edu.uy', '1971-12-19', 4, 'docente'),
    ('64159453', 'Pablo', 'Olivera', 'pablo.olivera@correo.ucu.edu.uy', '2006-05-12', 5, 'grado'),
    ('64424137', 'Lucas', 'Rodríguez', 'lucas.rodriguez@correo.ucu.edu.uy', '2007-11-16', 5, 'grado'),
    ('64667210', 'Rodrigo', 'González', 'rodrigo.gonzalez@correo.ucu.edu.uy', '1975-06-18', 6, 'docente'),
    ('64784642', 'Santiago', 'López', 'santiago.lopez@correo.ucu.edu.uy', '2006-11-23', 6, 'grado');

-- Torneo (se crea en inscripción, se cargan los planteles y luego pasa a en curso)
INSERT INTO torneo (id_torneo, nombre, anio, semestre, fecha_inicio, fecha_fin) VALUES
    (1, 'Torneo Interfacultades de Fútbol 5 - 2026/2', 2026, 2, '2026-08-17',
     GREATEST('2026-12-11', CURDATE() + INTERVAL 60 DAY));
INSERT INTO equipo (id_equipo, nombre, id_torneo, id_facultad) VALUES
    (1, 'Los Compiladores', 1, 1),
    (2, 'Bits FC', 1, 1),
    (3, 'Balance General', 1, 2),
    (4, 'Activo Corriente', 1, 2),
    (5, 'Jurisprudencia FC', 1, 3),
    (6, 'Bisturí FC', 1, 4),
    (7, 'Dialéctica United', 1, 5),
    (8, 'Inconsciente Colectivo', 1, 6);
INSERT INTO equipo_jugador_torneo (id_equipo, ci_jugador, id_torneo, numero_camiseta) VALUES
    (1, '41219379', 1, 21),
    (1, '41742762', 1, 1),
    (1, '41941007', 1, 12),
    (1, '42088771', 1, 3),
    (1, '42587642', 1, 23),
    (1, '42897431', 1, 10),
    (1, '43184132', 1, 7),
    (1, '43472949', 1, 5),
    (1, '43796981', 1, 18),
    (2, '44277071', 1, 20),
    (2, '44367036', 1, 8),
    (2, '44578639', 1, 5),
    (2, '44594708', 1, 4),
    (2, '44925511', 1, 11),
    (2, '45437977', 1, 16),
    (2, '45655496', 1, 23),
    (3, '45962318', 1, 3),
    (3, '46298954', 1, 13),
    (3, '46603466', 1, 9),
    (3, '47161570', 1, 20),
    (3, '47529697', 1, 10),
    (3, '47916054', 1, 4),
    (3, '48318045', 1, 12),
    (3, '48841472', 1, 16),
    (4, '49097880', 1, 16),
    (4, '49531424', 1, 4),
    (4, '49740433', 1, 18),
    (4, '50277956', 1, 17),
    (4, '50508422', 1, 8),
    (4, '50942581', 1, 12),
    (4, '51372567', 1, 15),
    (5, '51897284', 1, 19),
    (5, '52256594', 1, 12),
    (5, '52439243', 1, 3),
    (5, '52789595', 1, 21),
    (5, '52979041', 1, 20),
    (5, '53412193', 1, 16),
    (5, '53652848', 1, 10),
    (5, '53804754', 1, 9),
    (6, '54188193', 1, 22),
    (6, '54261389', 1, 8),
    (6, '54744783', 1, 6),
    (6, '54796667', 1, 11),
    (6, '55076436', 1, 14),
    (6, '55289532', 1, 17),
    (6, '55810559', 1, 20),
    (7, '56123761', 1, 11),
    (7, '56298639', 1, 22),
    (7, '56884303', 1, 16),
    (7, '57418486', 1, 13),
    (7, '57783784', 1, 23),
    (7, '57900027', 1, 6),
    (8, '58301230', 1, 7),
    (8, '58562957', 1, 15),
    (8, '58693184', 1, 8),
    (8, '58884606', 1, 12),
    (8, '59283651', 1, 20),
    (8, '59833523', 1, 14),
    (8, '60394449', 1, 13),
    (8, '60969436', 1, 23);
UPDATE equipo SET ci_capitan = '42587642' WHERE id_equipo = 1;
UPDATE equipo SET ci_capitan = '44594708' WHERE id_equipo = 2;
UPDATE equipo SET ci_capitan = '47529697' WHERE id_equipo = 3;
UPDATE equipo SET ci_capitan = '50277956' WHERE id_equipo = 4;
UPDATE equipo SET ci_capitan = '52979041' WHERE id_equipo = 5;
UPDATE equipo SET ci_capitan = '54796667' WHERE id_equipo = 6;
UPDATE equipo SET ci_capitan = '57418486' WHERE id_equipo = 7;
UPDATE equipo SET ci_capitan = '59283651' WHERE id_equipo = 8;
UPDATE torneo SET estado = 'en_curso' WHERE id_torneo = 1;

-- Fixture: fechas 1 a 5 (se crean como programados)
INSERT INTO partido (id_partido, id_torneo, numero_fecha, id_equipo_local, id_equipo_visitante, dia, id_turno, id_complejo, nombre_cancha) VALUES
    (1, 1, 1, 1, 8, '2026-09-14', 3, 1, 'Cancha 2'),
    (2, 1, 1, 7, 2, '2026-09-15', 4, 2, 'Central'),
    (3, 1, 1, 3, 6, '2026-09-16', 5, 2, 'Norte'),
    (4, 1, 1, 5, 4, '2026-09-17', 1, 3, 'Cancha A'),
    (5, 1, 2, 7, 1, '2026-09-28', 5, 2, 'Central'),
    (6, 1, 2, 8, 6, '2026-09-29', 1, 2, 'Norte'),
    (7, 1, 2, 5, 2, '2026-09-30', 2, 3, 'Cancha A'),
    (8, 1, 2, 3, 4, '2026-10-01', 3, 1, 'Cancha 1'),
    (9, 1, 3, 1, 6, '2026-10-12', 2, 2, 'Norte'),
    (10, 1, 3, 5, 7, '2026-10-13', 3, 3, 'Cancha A'),
    (11, 1, 3, 8, 4, '2026-10-14', 4, 1, 'Cancha 1'),
    (12, 1, 3, 3, 2, '2026-10-15', 5, 1, 'Cancha 2'),
    (13, 1, 4, 5, 1, CURDATE() - INTERVAL 1 DAY, 1, 3, 'Cancha A'),
    (14, 1, 4, 6, 4, CURDATE() - INTERVAL 2 DAY, 2, 1, 'Cancha 1'),
    (15, 1, 4, 3, 7, CURDATE() + INTERVAL 3 DAY, 1, 1, 'Cancha 2'),
    (16, 1, 4, 8, 2, CURDATE() + INTERVAL 4 DAY, 2, 2, 'Central'),
    (17, 1, 5, 1, 4, CURDATE() + INTERVAL 10 DAY, 1, 1, 'Cancha 1'),
    (18, 1, 5, 3, 5, CURDATE() + INTERVAL 10 DAY, 2, 1, 'Cancha 2'),
    (19, 1, 5, 6, 2, CURDATE() + INTERVAL 11 DAY, 1, 2, 'Central'),
    (20, 1, 5, 8, 7, CURDATE() + INTERVAL 11 DAY, 2, 2, 'Norte');

-- Sanción disciplinaria (cargada por la organización antes de la fecha 4)
INSERT INTO sancion_jugador (ci_jugador, id_torneo, motivo, numero_fecha_inicio, cantidad_fechas, observaciones) VALUES
    ('49740433', 1, 'disciplinaria', 4, 2, 'Agresión verbal al árbitro en la fecha 3');

-- Planillas, goles y tarjetas de los partidos disputados
INSERT INTO planilla_partido (id_partido, ci_jugador, id_equipo) VALUES
    (1, '41742762', 1),
    (1, '42088771', 1),
    (1, '42897431', 1),
    (1, '43184132', 1),
    (1, '41941007', 1),
    (1, '58693184', 8),
    (1, '60394449', 8),
    (1, '58301230', 8),
    (1, '59833523', 8),
    (1, '58562957', 8),
    (1, '58884606', 8);
INSERT INTO gol (id_partido, ci_jugador, minuto, autogol) VALUES
    (1, '41941007', 41, FALSE),
    (1, '58301230', 10, FALSE);
INSERT INTO tarjeta (id_partido, ci_jugador, minuto, color) VALUES
    (1, '41742762', 45, 'roja'),
    (1, '42088771', 12, 'amarilla'),
    (1, '58562957', 50, 'amarilla');
UPDATE partido SET estado = 'jugado' WHERE id_partido = 1;

INSERT INTO planilla_partido (id_partido, ci_jugador, id_equipo) VALUES
    (2, '57900027', 7),
    (2, '57783784', 7),
    (2, '56298639', 7),
    (2, '57418486', 7),
    (2, '56884303', 7),
    (2, '56123761', 7),
    (2, '44594708', 2),
    (2, '45437977', 2),
    (2, '44367036', 2),
    (2, '44277071', 2),
    (2, '44925511', 2);
INSERT INTO gol (id_partido, ci_jugador, minuto, autogol) VALUES
    (2, '56298639', 9, FALSE),
    (2, '56298639', 38, FALSE),
    (2, '56123761', 40, FALSE),
    (2, '44277071', 31, FALSE),
    (2, '44367036', 1, FALSE);
INSERT INTO tarjeta (id_partido, ci_jugador, minuto, color) VALUES
    (2, '57900027', 15, 'amarilla');
UPDATE partido SET estado = 'jugado' WHERE id_partido = 2;

INSERT INTO planilla_partido (id_partido, ci_jugador, id_equipo) VALUES
    (3, '47529697', 3),
    (3, '45962318', 3),
    (3, '47916054', 3),
    (3, '46298954', 3),
    (3, '47161570', 3),
    (3, '54796667', 6),
    (3, '54261389', 6),
    (3, '55076436', 6),
    (3, '55289532', 6),
    (3, '54744783', 6);
INSERT INTO gol (id_partido, ci_jugador, minuto, autogol) VALUES
    (3, '47161570', 27, FALSE),
    (3, '47161570', 44, FALSE),
    (3, '54261389', 7, FALSE),
    (3, '54796667', 18, FALSE),
    (3, '55289532', 3, FALSE);
UPDATE partido SET estado = 'jugado' WHERE id_partido = 3;

INSERT INTO planilla_partido (id_partido, ci_jugador, id_equipo) VALUES
    (4, '53652848', 5),
    (4, '52439243', 5),
    (4, '51897284', 5),
    (4, '52789595', 5),
    (4, '52979041', 5),
    (4, '53412193', 5),
    (4, '51372567', 4),
    (4, '49740433', 4),
    (4, '50942581', 4),
    (4, '50277956', 4),
    (4, '49097880', 4),
    (4, '49531424', 4);
INSERT INTO gol (id_partido, ci_jugador, minuto, autogol) VALUES
    (4, '53412193', 26, FALSE),
    (4, '49097880', 4, FALSE),
    (4, '50277956', 5, FALSE);
UPDATE partido SET estado = 'jugado' WHERE id_partido = 4;

INSERT INTO planilla_partido (id_partido, ci_jugador, id_equipo) VALUES
    (5, '56298639', 7),
    (5, '56123761', 7),
    (5, '57900027', 7),
    (5, '57418486', 7),
    (5, '56884303', 7),
    (5, '57783784', 7),
    (5, '42088771', 1),
    (5, '41941007', 1),
    (5, '41219379', 1),
    (5, '42897431', 1),
    (5, '43184132', 1),
    (5, '42587642', 1),
    (5, '43472949', 1);
INSERT INTO gol (id_partido, ci_jugador, minuto, autogol) VALUES
    (5, '56884303', 9, FALSE),
    (5, '56884303', 14, FALSE),
    (5, '41219379', 50, FALSE),
    (5, '43472949', 46, FALSE),
    (5, '42897431', 9, FALSE),
    (5, '43184132', 44, FALSE);
INSERT INTO tarjeta (id_partido, ci_jugador, minuto, color) VALUES
    (5, '42088771', 25, 'amarilla');
UPDATE partido SET estado = 'jugado' WHERE id_partido = 5;

INSERT INTO planilla_partido (id_partido, ci_jugador, id_equipo) VALUES
    (6, '60394449', 8),
    (6, '58301230', 8),
    (6, '58693184', 8),
    (6, '59283651', 8),
    (6, '59833523', 8),
    (6, '58884606', 8),
    (6, '58562957', 8),
    (6, '55289532', 6),
    (6, '54744783', 6),
    (6, '54261389', 6),
    (6, '54796667', 6),
    (6, '54188193', 6),
    (6, '55810559', 6),
    (6, '55076436', 6);
INSERT INTO gol (id_partido, ci_jugador, minuto, autogol) VALUES
    (6, '58884606', 10, FALSE),
    (6, '59283651', 42, FALSE),
    (6, '59833523', 32, FALSE),
    (6, '55289532', 20, FALSE),
    (6, '54744783', 33, FALSE),
    (6, '54261389', 35, FALSE),
    (6, '55289532', 30, FALSE),
    (6, '55810559', 48, FALSE),
    (6, '55289532', 33, TRUE);
INSERT INTO tarjeta (id_partido, ci_jugador, minuto, color) VALUES
    (6, '58884606', 23, 'amarilla');
UPDATE partido SET estado = 'jugado' WHERE id_partido = 6;

INSERT INTO planilla_partido (id_partido, ci_jugador, id_equipo) VALUES
    (7, '53412193', 5),
    (7, '52789595', 5),
    (7, '52256594', 5),
    (7, '52979041', 5),
    (7, '51897284', 5),
    (7, '52439243', 5),
    (7, '44594708', 2),
    (7, '44367036', 2),
    (7, '44578639', 2),
    (7, '45437977', 2),
    (7, '44925511', 2),
    (7, '45655496', 2),
    (7, '44277071', 2);
INSERT INTO gol (id_partido, ci_jugador, minuto, autogol) VALUES
    (7, '52256594', 46, FALSE),
    (7, '52789595', 20, FALSE),
    (7, '45437977', 36, FALSE),
    (7, '44925511', 31, FALSE),
    (7, '44594708', 14, FALSE);
INSERT INTO tarjeta (id_partido, ci_jugador, minuto, color) VALUES
    (7, '52256594', 46, 'amarilla');
UPDATE partido SET estado = 'jugado' WHERE id_partido = 7;

INSERT INTO planilla_partido (id_partido, ci_jugador, id_equipo) VALUES
    (8, '48318045', 3),
    (8, '46603466', 3),
    (8, '47916054', 3),
    (8, '47529697', 3),
    (8, '46298954', 3),
    (8, '45962318', 3),
    (8, '47161570', 3),
    (8, '50277956', 4),
    (8, '49740433', 4),
    (8, '50942581', 4),
    (8, '51372567', 4),
    (8, '49097880', 4),
    (8, '50508422', 4),
    (8, '49531424', 4);
INSERT INTO gol (id_partido, ci_jugador, minuto, autogol) VALUES
    (8, '47916054', 30, FALSE),
    (8, '47529697', 39, FALSE),
    (8, '45962318', 38, FALSE);
INSERT INTO tarjeta (id_partido, ci_jugador, minuto, color) VALUES
    (8, '46298954', 30, 'amarilla'),
    (8, '50942581', 18, 'amarilla'),
    (8, '49097880', 3, 'amarilla'),
    (8, '50508422', 29, 'amarilla');
UPDATE partido SET estado = 'jugado' WHERE id_partido = 8;

INSERT INTO planilla_partido (id_partido, ci_jugador, id_equipo) VALUES
    (9, '42088771', 1),
    (9, '43472949', 1),
    (9, '43184132', 1),
    (9, '42897431', 1),
    (9, '42587642', 1),
    (9, '41941007', 1),
    (9, '55076436', 6),
    (9, '54188193', 6),
    (9, '54261389', 6),
    (9, '54744783', 6),
    (9, '55289532', 6),
    (9, '54796667', 6);
INSERT INTO tarjeta (id_partido, ci_jugador, minuto, color) VALUES
    (9, '42088771', 39, 'amarilla'),
    (9, '43184132', 3, 'amarilla'),
    (9, '42587642', 39, 'amarilla');
UPDATE partido SET estado = 'jugado' WHERE id_partido = 9;

INSERT INTO planilla_partido (id_partido, ci_jugador, id_equipo) VALUES
    (10, '52789595', 5),
    (10, '53412193', 5),
    (10, '52256594', 5),
    (10, '53652848', 5),
    (10, '51897284', 5),
    (10, '52979041', 5),
    (10, '52439243', 5),
    (10, '56884303', 7),
    (10, '57783784', 7),
    (10, '56298639', 7),
    (10, '57418486', 7),
    (10, '56123761', 7);
INSERT INTO gol (id_partido, ci_jugador, minuto, autogol) VALUES
    (10, '52439243', 8, FALSE),
    (10, '51897284', 31, FALSE),
    (10, '57418486', 34, FALSE),
    (10, '56884303', 32, FALSE),
    (10, '57783784', 25, FALSE);
INSERT INTO tarjeta (id_partido, ci_jugador, minuto, color) VALUES
    (10, '56884303', 12, 'roja');
UPDATE partido SET estado = 'jugado' WHERE id_partido = 10;

INSERT INTO planilla_partido (id_partido, ci_jugador, id_equipo) VALUES
    (11, '58301230', 8),
    (11, '59283651', 8),
    (11, '58693184', 8),
    (11, '58562957', 8),
    (11, '59833523', 8),
    (11, '60394449', 8),
    (11, '58884606', 8),
    (11, '50277956', 4),
    (11, '49097880', 4),
    (11, '50942581', 4),
    (11, '51372567', 4),
    (11, '49531424', 4),
    (11, '50508422', 4);
INSERT INTO gol (id_partido, ci_jugador, minuto, autogol) VALUES
    (11, '58301230', 17, FALSE),
    (11, '49097880', 34, FALSE),
    (11, '50942581', 24, FALSE),
    (11, '50277956', 17, FALSE);
INSERT INTO tarjeta (id_partido, ci_jugador, minuto, color) VALUES
    (11, '49097880', 45, 'amarilla'),
    (11, '50508422', 13, 'amarilla');
UPDATE partido SET estado = 'jugado' WHERE id_partido = 11;

INSERT INTO planilla_partido (id_partido, ci_jugador, id_equipo) VALUES
    (13, '53412193', 5),
    (13, '52789595', 5),
    (13, '51897284', 5),
    (13, '52439243', 5),
    (13, '52979041', 5),
    (13, '53652848', 5),
    (13, '52256594', 5),
    (13, '41742762', 1),
    (13, '41219379', 1),
    (13, '41941007', 1),
    (13, '43184132', 1),
    (13, '43472949', 1),
    (13, '42897431', 1);
INSERT INTO gol (id_partido, ci_jugador, minuto, autogol) VALUES
    (13, '43472949', 11, FALSE),
    (13, '43472949', 41, FALSE),
    (13, '43472949', 38, FALSE);
INSERT INTO tarjeta (id_partido, ci_jugador, minuto, color) VALUES
    (13, '51897284', 23, 'amarilla'),
    (13, '53652848', 3, 'amarilla'),
    (13, '52256594', 25, 'amarilla');
UPDATE partido SET estado = 'jugado' WHERE id_partido = 13;

-- Partidos postergados y cancelados
UPDATE partido SET estado = 'postergado' WHERE id_partido = 12;
UPDATE partido SET estado = 'cancelado' WHERE id_partido = 15;
