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
	`estado`	varchar(10) NOT NULL DEFAULT 'n',
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
