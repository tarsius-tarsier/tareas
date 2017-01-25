CREATE TABLE proyecto(
	id integer primary key autoincrement,
	nombre varchar(30) not null unique
);
CREATE TABLE lapso(
	id integer primary key autoincrement,
	tarea_id integer references tarea(id) not null,
	creado integer not null,
	modificado integer,
	inicio integer not null,
	termino integer
);
CREATE TABLE log(
	id integer primary key autoincrement,
	tarea_id integer references tarea(id) not null,
	creado integer not null,
	log text not null
);
CREATE TABLE "tarea" (
	`id`	integer PRIMARY KEY AUTOINCREMENT,
	`nombre`	varchar(255) NOT NULL,
	`estado`	varchar(10) NOT NULL DEFAULT 'N',
	`proyecto_id`	integer,
	`creada`	integer NOT NULL DEFAULT (strftime('%s','now')),
	`iniciada`	integer,
	`terminada`	integer,
	`modificada`	integer,
	`hh_estimadas`	real,
	`notas`	text,
	`fecha_limite`	INTEGER,
	FOREIGN KEY(`proyecto_id`) REFERENCES `proyecto`(`id`)
);
CREATE TABLE estado_del_arte (
	id integer primary key autoincrement,
	proyecto_id integer references proyecto(id),
	fecha integer not null,
	creado integer not null default (strftime('%s','now')),
	frecuencia varchar(20) not null default 'diaria',
	modificado integer,
	cerrado boolean default false,
	unique(frecuencia,fecha,proyecto_id)
);
CREATE TABLE observacion (
	id integer primary key autoincrement,
	observacion text not null,
	tipo varchar(2) not null default 't',
	tarea_id integer references tarea(id),
	estado_del_arte_id integer references estado_del_arte(id),
	prioridad integer not null default 1,
	completado boolean default false,
	creado integer not null default (strftime('%s','now')),
	modificado integer,
	observacion_id integer references observacion(id)
);
