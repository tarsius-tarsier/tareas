#!/usr/bin/env python
import sqlite3
import argparse
import time
import shutil
import os
import datetime
import json
from string import Template

def carga_config():
   """ carga archivo de configuracion desde archivo """
   config = {}
   for loc in os.curdir, os.path.join(os.path.expanduser("~"),'.tareas'), "/etc/tareas", os.environ.get("TAREAS_CONF_DIR"):
       try:
           if loc is not None:
               ruta_config = os.path.join(loc,"config.json")
               if os.path.exists(ruta_config):
                   with open(ruta_config) as f:
                       config = json.loads(f.read())
                       break
       except IOError:
           pass
   return config

def conexion_db(ruta_db=None):
    """ conexion a base  de datos """
    if ruta_db is None:
        for loc in os.curdir, os.path.join(os.path.expanduser("~"),'.tareas'), "/etc/tareas", os.environ.get("TAREAS_CONF_DIR"):
            try:
                if loc is not None:
                    ruta_db = os.path.join(loc,"tareas.db")
                    if os.path.exists(ruta_db):
                        ruta_db = os.path.join(loc,"tareas.db")
                        break
            except IOError:
                pass
    return sqlite3.connect(ruta_db)

config = carga_config()

ruta_db = None
if 'ruta_db' in config:
    ruta_db = config['ruta_db']

conexion    = conexion_db(ruta_db)
cursor      = conexion.cursor()

ruta_archivos = None
if 'archivados' in config:
    ruta_archivos = config['archivados']
else:
    ruta_archivos  = os.path.join(os.path.expanduser('~'),'workspace')

if 'activo' in config:
    escritorio = config['activo']
else:
    escritorio  = os.path.join(os.path.expanduser('~'),'Desktop')

CURSANDO  = 'c'
TERMINADO = 't'
NUEVO     = 'n'
PAUSADO   = 'p'

OBS_RIESGO  = 'r'
OBS_TODO    = 't'
OBS_AMENAZA = 'a'
OBS_NORMAL  = 'o'
OBS_PASADO  = 'p'
OBS_RETRASO  = 'e'

def proyectos(imprimir=True):
    cursor.execute('select * from proyecto order by nombre')
    r = cursor.fetchall()
    proyectos = []
    if imprimir:
        print encabezado_proyecto()
    for fila in r:
        p = Proyecto(tupla=fila)
        if imprimir:
            print p.formatear()
        proyectos.append(p)
    return proyectos

def get_observaciones(tipo=OBS_TODO,completado=False,desde=None,hasta=None,proyectos=None,ordenadas=None):
    if ordenadas is None:
        ordenadas = 'creado asc'
    filtros = ['completado=?','tipo=?']
    valores = [OBS_RETRASO,completado,tipo]
    if proyectos is not None:
        filtros  += ['proyecto_id in({})'.format(','.join('?' for x in proyectos))]
        valores  += proyectos

    if desde is not None:
        filtros  += ['termino>=?)']
        valores  += [desde]

    if hasta is not None:
        filtros  += ['termino<=?']
        valores  += [hasta]

    query = ('select o.id, '
             '       o.observacion, '
             '       o.tipo, '
             '       o.prioridad, '
             '       o.completado, '
             '       o.creado, '
             '       o.estado_del_arte_id, '
             '       o.modificado, '
             '       o.tarea_id, '
             '       (select count(*) from observacion where observacion_id=o.id and tipo=?) as postpuesto, '
             '       t.proyecto_id '
             'from observacion o left join tarea t on o.tarea_id=t.id '
             )

    query += 'where '
    query = '{}{} order by {}'.format(query,' and '.join(filtros),ordenadas)
    cursor.execute(query,valores)
    return [Observacion(tupla=r) for r in cursor.fetchall()]

def tareas(imprimir=True,proyectos=None,estados=None,desde=None,hasta=None):
    query = 'select * from tarea ';
    filtros = []
    valores = []

    if proyectos is not None:
        filtros  += ['proyecto_id in({})'.format(','.join('?' for x in proyectos))]
        valores  += proyectos

    if estados is not None:
        filtros  += ['estado in({})'.format(','.join('?' for x in estados))]
        valores  += estados

    if desde is not None:
        filtros  += ['id in(select distinct tarea_id from lapso where termino>=?)']
        valores  += [desde]

    if hasta is not None:
        filtros  += ['id in(select distinct tarea_id from lapso where termino<=?)']
        valores  += [hasta]

    if len(filtros) > 0:
        query += 'where '

    query = '{}{} order by creada asc'.format(query,' and '.join(filtros))
    cursor.execute(query, valores)
    r = cursor.fetchall()
    if imprimir:
        print encabezado_tarea(desde=desde,hasta=hasta)
    tareas = []
    for fila in r:
        t = Tarea(tupla=fila)
        if imprimir:
            print t.formatear(desde=desde,hasta=hasta)
        tareas.append(t)
    return tareas

class Proyecto():
    def __init__(self,tupla=None,id=None,nombre=None):
        self.id     = None
        self.nombre = None

        if tupla is not None:
            self.desde_tupla(tupla)

    def desde_tupla(self,tupla):
        self.id     = tupla[0]
        self.nombre = tupla[1]

    def formatear(self):
        return '{}\t{}'.format(self.id,self.nombre)

def convierte_a_unix(fecha):
    try:
       r = time.mktime(datetime.datetime.strptime(fecha, '%Y-%m-%d %H:%M:%S').timetuple()) 
    except:
       r = None
    return r

def convierte_desde_unix(unix):
    return datetime.datetime.fromtimestamp(int(unix))

class Tarea():
    def __init__(self,id=None,tupla=None,nombre=None,proyecto=None,estimacion=None,fecha_limite=None):
        self.id           = id
        self.nombre       = nombre
        self.proyecto_id  = proyecto
        self.estimacion   = estimacion
        self.fecha_limite = None
        self.observaciones = []
        fecha_limite_string = fecha_limite
        if fecha_limite_string is not None:
            self.fecha_limite = convierte_a_unix(fecha_limite_string)
        if id is not None:
            self.desde_db(id)
        if tupla is not None:
            self.desde_tupla(tupla)

    def carga_observaciones(self):
        self.observaciones = []
        query = ('select id, '
                 '       observacion, '
                 '       tipo, '
                 '       prioridad, '
                 '       completado, '
                 '       creado, '
                 '       estado_del_arte_id, '
                 '       modificado, '
                 '       tarea_id '
                 'from observacion where tarea_id=? order by tipo asc,prioridad asc')
        cursor.execute(query,[self.id])
        res = cursor.fetchall()
        for r in res:
            o = Observacion(tupla=r)
            self.observaciones += [o]

    def eliminar(self,id):
        cursor.execute("delete from log where tarea_id=?",(id, ))
        cursor.execute("delete from lapso where tarea_id=?",(id, ))
        cursor.execute("delete from observacion where tarea_id=?", (id, ))
        cursor.execute("delete from tarea where id=?", (id, ))
        conexion.commit()

    def editar(self,nombre=None,fecha_limite=None,estimacion=None):
        ahora = int(time.time())
        if estimacion is not None:
            cursor.execute("update tarea set hh_estimadas=?,modificada=? where id=?", (estimacion,ahora,self.id))
            log    = 'insert into log (tarea_id,creado,log) values(?,?,?)'
            cursor.execute(log,(self.id,ahora,'editando hh estimadas'))
            conexion.commit()
        if fecha_limite is not None:
            fecha_limite_string = fecha_limite
            if fecha_limite_string is not None:
                fecha_limite = convierte_a_unix(fecha_limite_string)
            cursor.execute("update tarea set fecha_limite = ?,modificada=? where id=?", (fecha_limite,ahora,self.id))
            log    = 'insert into log (tarea_id,creado,log) values(?,?,?)'
            cursor.execute(log,(self.id,ahora,'editando fecha limite'))
            conexion.commit()
        if nombre is not None:
            cursor.execute("update tarea set nombre = ?,modificada=? where id=?", (nombre,ahora,self.id))
            log    = 'insert into log (tarea_id,creado,log) values(?,?,?)'
            cursor.execute(log,(self.id,ahora,'editando nombre'))
            conexion.commit()
        self.desde_db(self.id)

    def guardar(self):
        cursor.execute("insert into tarea (nombre,hh_estimadas,proyecto_id,estado,fecha_limite) values (?,?,?,?,?)",
                       (self.nombre, self.estimacion, self.proyecto_id,NUEVO,self.fecha_limite))
        conexion.commit()
        self.desde_db(cursor.lastrowid)

    def desde_tupla(self,tupla):
        if tupla is None:
             self.id           = None
             self.nombre       = None
             self.estado       = None
             self.proyecto_id  = None
             self.creado       = None
             self.iniciada     = None
             self.terminada    = None
             self.modificada   = None
             self.hh_estimadas = None
             self.notas        = None
             self.fecha_limite = None
        else:
             self.id           = tupla[0]
             self.nombre       = tupla[1]
             self.estado       = tupla[2]
             self.proyecto_id  = tupla[3]
             self.creado       = tupla[4]
             self.iniciada     = tupla[5]
             self.terminada    = tupla[6]
             self.modificada   = tupla[7]
             self.hh_estimadas = tupla[8]
             self.notas        = tupla[9]
             self.fecha_limite = tupla[10]

    def recuperar(self,id):
        self.desde_db(id)
        if self.id is not None:
            origen   = os.path.join(ruta_archivos,str(self.id))
            archivos = os.listdir(origen)
            for a in archivos:
                shutil.move(os.path.join(origen,a), escritorio)

    def archivar(self,id):
        self.desde_db(id)
        if self.id is not None:
            archivos = os.listdir(escritorio)
            for a in archivos:
                destino = os.path.join(ruta_archivos,str(self.id))
                if not os.path.isdir(destino):
                    os.mkdir(destino)
                shutil.move(os.path.join(escritorio,a), destino)

    def desde_db(self,id):
        select = 'select * from tarea where id=?';
        cursor.execute(select,(id,))
        r = cursor.fetchone()
        self.desde_tupla(r)

    def resta(self):
        ahora = datetime.datetime.now()
        if self.fecha_limite is None:
            return '-'
        fecha_limite = convierte_desde_unix(self.fecha_limite)
        diferencia = fecha_limite-ahora
        if self.terminada and self.estado == TERMINADO: 
            diferencia = fecha_limite - convierte_desde_unix(self.terminada)
        return '{}'.format(round((diferencia.total_seconds()/86400.0),1))

    def diferencia(self):
        estimadas = self.hh_estimadas
        hh = self.hh()
        if estimadas is None:
            return None
        return (estimadas-hh)

    def hh(self,desde=None,hasta=None,alias=None):
        query = "select round(sum(cast(coalesce(termino,strftime('%s','now')) as real) - cast(inicio as real))/3600,2) from lapso where tarea_id=? "
        values = [self.id]
        if desde is not None:
            query += 'and inicio>=? '
            values += [desde]
        if hasta is not None:
            query += 'and termino<=? '
            values += [hasta]
        cursor.execute(query,values)
        r = cursor.fetchone()
        if r is not None:
            if r[0] is not None:
                return r[0]
        return 0

    def iniciar(self):
        """ cambia el estado de una tarea a cursando """
        ahora = int(time.time())
        update = 'update tarea set estado=?,iniciada=?,modificada=? where id=? and estado in (?,?,?) and estado !=?'
        cursor.execute(update,(CURSANDO,ahora,ahora,self.id,NUEVO,PAUSADO,TERMINADO,CURSANDO))
        if cursor.rowcount > 0:
            # crea entrada en log
            log    = 'insert into log (tarea_id,creado,log) values(?,?,?)'
            cursor.execute(log,(self.id,ahora,'iniciando'))
            # crea entrada en lapso
            lapso  = 'insert into lapso (tarea_id,inicio,creado) values(?,?,?)'
            cursor.execute(lapso,(self.id,ahora,ahora))
            conexion.commit()
        else:
            print 'id:{}\tsin cambios'.format(self.id)

    def terminar(self):
        ahora = int(time.time())
        update = 'update tarea set estado=?,terminada=?,modificada=? where id=? and estado in (?,?) and estado !=?'
        cursor.execute(update,(TERMINADO,ahora,ahora,self.id,CURSANDO,PAUSADO,TERMINADO))
        if cursor.rowcount > 0:
            # crea entrada en log
            log    = 'insert into log (tarea_id,creado,log) values(?,?,?)'
            cursor.execute(log,(self.id,ahora,'terminando'))
            # crea entrada en lapso
            lapso  = 'update lapso set modificado=?,termino=? where termino is null and tarea_id=?'
            cursor.execute(lapso,(ahora,ahora,self.id))
            conexion.commit()
        else:
            print 'id:{}\tsin cambios'.format(self.id)

    def pausar(self):
        # cambia estado a p (pausado)
        ahora = int(time.time())
        update = 'update tarea set estado=?,modificada=? where id=? and estado=? and estado !=?'
        cursor.execute(update,(PAUSADO,ahora,self.id,CURSANDO,PAUSADO))
        if cursor.rowcount > 0:
            # crea entrada en log
            log    = 'insert into log (tarea_id,creado,log) values(?,?,?)'
            cursor.execute(log,(self.id,ahora,'pausando'))
            # actualiza entrada en lapso
            lapso  = 'update lapso set modificado=?,termino=? where termino is null and tarea_id=? '
            cursor.execute(lapso,(ahora,ahora,self.id))
            conexion.commit()
        else:
            print 'id:{}\tsin cambios'.format(self.id)

    def formatear(self,detalle=False,desde=None,hasta=None):
        if self.id is None:
            return ''
        hhp = ''
        if desde is not None or hasta is not None:
            hhp = '{}\t'.format(self.hh(desde=desde,hasta=hasta))
        dif = '-'
        if self.hh_estimadas is not None:
            dif = self.diferencia()

        if detalle:
            termino = ''
            if self.estado == TERMINADO and self.terminada is not None:
                t = convierte_desde_unix(self.terminada)
                termino = 'ft:\t{}\n'.format(t)
            if self.fecha_limite is None:
                fl = ''
            else:
                fl = convierte_desde_unix(self.fecha_limite)
            self.carga_observaciones()
            obs_str =  '\n'.join([o.formatear() for o in self.observaciones])
            return 'id:\t{}\npid:\t{}\nnombre:\t{}\nestado:\t{}\nhh:\t{}\nest:\t{}\ndif:\t{}\n{}fl:\t{}\nr:\t{}\nobs:\n{}'.format(
                    self.id,
                    self.proyecto_id,
                    self.nombre,
                    self.estado,
                    self.hh(),
                    self.hh_estimadas,
                    dif,
                    termino,
                    fl,
                    self.resta(),obs_str)
        else:
            return '{}\t{}\t{}\t{}\t{}{}\t{}\t{}'.format(self.id,self.proyecto_id,self.estado,self.hh(),hhp,dif,self.resta(),self.nombre)

def pausar_todo():
    lista = tareas(imprimir=False,estados=[CURSANDO])
    for t in lista:
        t.pausar()

def encabezado_proyecto():
    return 'id\tnombre'

def encabezado_tarea(desde=None,hasta=None):
    hhp = ''
    if desde is not None or hasta is not None:
        hhp = 'hhp\t'
    return 'id\tpid\testado\thh\t{}dif\tr\ttarea'.format(hhp)

class EstadoDelArte():
    def __init__(self,pid=None,fecha=None,carga=True):
        self.proyecto_id = pid
        self.fecha       = fecha
        self.creado      = None
        self.modificado  = None
        self.frecuencia  = None
        self.todo        = []
        self.riesgos     = []
        self.amenazas    = []
        if carga:
            self.carga()
            self.carga_observaciones()

    def anexa_observacion(self,tarea_id):
        query = 'update observacion set estado_del_arte_id=? where id=?'
        valores = [self.id,tarea_id]
        cursor.execute(query,valores)
        conexion.commit()

    def get_todo(self,imprimir=True):
        for t in self.todo:
            if imprimir:
                print t.formatear()

    def get_amenazas(self,imprimir=True):
        for a in self.amenazas:
            if imprimir:
                print a.formatear()

    def get_riesgos(self,imprimir=True):
        for r in self.riesgos:
            if imprimir:
                print r.formatear()

    def carga_observaciones(self):
        query = ('select id, '
                 '       observacion, '
                 '       tipo, '
                 '       prioridad, '
                 '       completado, '
                 '       creado, '
                 '       estado_del_arte_id, '
                 '       modificado, '
                 '       tarea_id '
                 'from observacion where estado_del_arte_id=? order by prioridad asc')
        cursor.execute(query,[self.id])
        resultado = cursor.fetchall()
        for r in resultado:
            i = Observacion(tupla=r)
            if i.tipo == OBS_TODO:
                self.todo    += [i]
            if i.tipo == OBS_RIESGO:
                self.riesgos += [i]
            if i.tipo == OBS_AMENAZA:
                self.amenaza += [i]

    def plantilla(self):
        "devuelve la plantilla"
        f = open('plantilla.txt')
        src = Template(f.read())
        f.close()
        d = {'fecha': convierte_desde_unix(self.fecha).strftime('%Y-%m-%d'),
             'frecuencia':self.frecuencia,
             'todo':"".join([t.plantilla() for t in self.todo]),
             'amenazas':"".join([t.plantilla() for t in self.amenazas]),
             'riesgos':"".join([r.plantilla() for r in self.riesgos])}
        return src.substitute(d)

    def formatear(self):
        f = convierte_desde_unix(self.fecha).strftime('%Y-%m-%d')
        return 'fecha:\t{}\npid\t{}'.format(f,self.proyecto_id)

    def carga(self):
        "carga un plan, si este no existe lo crea"
        query = ('select id,proyecto_id,fecha,creado,modificado '
                 'from estado_del_arte where fecha=? and proyecto_id=?')
        valores = [self.fecha,self.proyecto_id]
        cursor.execute(query,valores)
        r = cursor.fetchone()
        if r is None:
            id = self.crea()
        else:
            id = r[0]
        self.desde_db(id)

    def crea(self):
        "crea un estado_del_arte devolviendo el id"
        query   = 'insert into estado_del_arte (proyecto_id,fecha) values (?,?)'
        valores = [self.proyecto_id,self.fecha]
        cursor.execute(query,valores)
        conexion.commit()
        return cursor.lastrowid

    def desde_db(self,id):
        "inicializa los atributos de un plan"
        query = ('select id,proyecto_id,fecha,creado,modificado,frecuencia '
                 'from estado_del_arte where id=?')
        valores = [id]
        cursor.execute(query,valores)
        r = cursor.fetchone()
        self.id          = r[0]
        self.proyecto_id = r[1]
        self.fecha       = r[2]
        self.creado      = r[3]
        self.modificado  = r[4]
        self.frecuencia  = r[5]

    def agrega_observacion(self,observacion,tipo=None,prioridad=None):
        "agrega una observacion al plan"
        o = Observacion()
        o.crea()

    def elimina(self,id):
        "elimina una observacion del estado del arte"

class Observacion():
    def __init__(self,id=None,tupla=None):
        self.id          = id
        self.observacion = None
        self.tipo        = OBS_TODO
        self.prioridad   = 1
        self.completado  = False
        self.estado_del_arte_id = None
        self.tarea_id    = None
        self.postpuesto  = 0
        if tupla is not None:
            self.desde_tupla(tupla)

    def formatear_todo(self):
        return '{}\t{}\t{}\t{}'.format(self.id,self.prioridad,self.tarea_id,self.observacion)

    def formatear(self):
        return '{}\t{}\t{}\t{}\t{}\t{}\t{}'.format(self.id,self.completado,self.prioridad,self.tipo,self.tarea_id,self.postpuesto,self.observacion)
    
    def completa(self,comentario=None):
        ahora = int(time.time())
        query = 'update observacion set completado=?,modificado=? where id=?'
        valores = [True,ahora,self.id]
        cursor.execute(query,valores)
        conexion.commit()
        if comentario is not None:
            o = Observacion()
            o.observacion = comentario
            o.tipo = OBS_PASADO
            o.tarea_id  = self.obtiene_tarea_id()
            o.crea()

    def baja_prioridad(self):
        """baja la prioridad de observacion"""
        ahora = int(time.time())
        update="update observacion set prioridad=(prioridad-1), modificado=? where id=?"
        cursor.execute(update,[ahora,self.id])
        conexion.commit()

    def sube_prioridad(self):
        """sube la prioridad de observacion"""
        ahora = int(time.time())
        update="update observacion set prioridad=(prioridad+1), modificado=? where id=?"
        cursor.execute(update,[ahora,self.id])
        conexion.commit()

    def obtiene_tarea_id(self):
        select = "select tarea_id from observacion where id=?"
        values = [self.id]
        cursor.execute(select,values)
        r = cursor.fetchone()
        if r is not None:
            return r[0]
        
    def postponer(self,motivo):
        """postpone una tarea"""
        ahora = int(time.time())
        modifica = 'update observacion set modificado=? where id=?'
        valores = [ahora,self.id]
        cursor.execute(modifica,valores)
        postpone = 'insert into observacion (observacion,tipo,creado,observacion_id) values (?,?,?,?) ' 
        valores = [motivo,OBS_RETRASO,ahora,self.id]
        cursor.execute(postpone,valores)
        conexion.commit()

    def plantilla(self):
        "devuelve la plantilla cargada"
        f = open('plantilla_obs.txt')
        src = Template(f.read())
        f.close()

        tarea = '[{}] '.format(self.tarea_id)
        if self.tarea_id is None:
            tarea = ''

        d = {'tarea_id': self.tarea_id,
             'prioridad':self.prioridad,
             'tarea':tarea,
             'observacion':self.observacion}
        return src.substitute(d)

    def desde_tupla(self,r):
        self.id                 = r[0]
        self.observacion        = r[1]
        self.tipo               = r[2]
        self.prioridad          = r[3]
        self.completado         = r[4]
        self.creado             = r[5]
        self.estado_del_arte_id = r[6]
        self.modificado         = r[7]
        self.tarea_id           = r[8]
        if len(r) > 9:
            self.postpuesto     = r[9]
        if len(r) > 10:
            self.proyecto_id    = r[10]

    def formatea(self):
        "formatea"
        return 'id:\t{}\ttipo:\t{}\tcom:\t{}\tobs:\t{}'.format(self.id,self.tipo,self.completado,self.obs)

    def crea(self):
        "la logica necesaria para crear una observacion"
        insert   = ('insert into observacion (observacion, '
                                             'tipo, '
                                             'prioridad, '
                                             'estado_del_arte_id, '
                                             'tarea_id, '
                                             'completado) '
                    'values (?,?,?,?,?,?) ')
        valores = [self.observacion,
                   self.tipo,
                   self.prioridad,
                   self.estado_del_arte_id,
                   self.tarea_id,
                   self.completado]
        cursor.execute(insert,valores)
        conexion.commit()

def main():
    p = argparse.ArgumentParser()
    p.add_argument('-P','--proyectos', action='store_true',help='lista de proyectos')
    p.add_argument('-i','--iniciar', help='inicia una tarea')
    p.add_argument('-t','--terminar',help='termina una tarea')
    p.add_argument('-v','--ver',help='ver tarea')
    p.add_argument('-l','--tareas',action='store_true',help='listar tareas')
    p.add_argument('-p','--pausar',  help='pausa una tarea')
    p.add_argument('-e','--elimina',  help='elimina una tarea')
    p.add_argument('-a','--agrega',  help='agrega una tarea')
    p.add_argument('-pid','--proyecto',  help='id de proyecto')
    p.add_argument('-hh','--horashombre',  help='horas hombre')
    p.add_argument('-A','--archiva', help='archiva escritorio')
    p.add_argument('-r','--recupera', help='recupera archivos')
    p.add_argument('-E','--estimacion', type=float,help='estimacion en hh')
    p.add_argument('-f','--fechalimite', help='fecha limite en formato yyyy-mm-dd hh:mm')
    p.add_argument('-S','--pausatodas',action='store_true',help='pausa todas las tareas en curso')
    p.add_argument('-fe','--filtroestado',action='append',help='filtro estado')
    p.add_argument('-fp','--filtroproyecto',type=int,action='append',help='filtro proyecto')
    p.add_argument('-s','--editar',help='edita tarea')
    p.add_argument('-n','--nombre',help='nuevo nombre de tarea')
    p.add_argument('-de','--desde',help='desde')
    p.add_argument('-ha','--hasta',help='hasta')
    p.add_argument('-o','--observacion',help='observacion')
    p.add_argument('-or','--observacionriesgo',action='store_true',help='observacion de riesgo')
    p.add_argument('-ot','--observaciontodo',action='store_true',help='observacion todo')
    p.add_argument('-oa','--observacionamenaza',action='store_true',help='observacion amenaza')
    p.add_argument('-oo','--observacionnormal',action='store_true',help='observacion normal')
    p.add_argument('-op','--observacionpasado',action='store_true',help='observacion en pasado')
    p.add_argument('-oP','--observacionprioridad',help='observacion prioridad')
    a = p.parse_args()
    if a.archiva:
        t = Tarea()
        t.archivar(a.archiva)
    elif a.elimina:
        t = Tarea()
        t.eliminar(a.elimina)
    elif a.recupera:
        t = Tarea()
        t.recuperar(a.recupera)
    elif a.iniciar:
        if a.pausatodas:
            pausar_todo()
        t = Tarea(a.iniciar)
        t.iniciar()
    elif a.terminar:
        t = Tarea(a.terminar)
        t.terminar()
    elif a.pausar:
        t = Tarea(a.pausar)
        t.pausar()
    elif a.horashombre:
        t = Tarea(a.horashombre)
        print t.hh(desde=convierte_a_unix(a.desde),hasta=convierte_a_unix(a.hasta))
    elif a.proyectos:
        proyectos()
    elif a.ver:
        t = Tarea(a.ver)
        print t.formatear(detalle=True)
    elif a.agrega:
        t = Tarea(nombre=a.agrega,proyecto=a.proyecto,estimacion=a.estimacion,fecha_limite=a.fechalimite)
        t.guardar()
        print t.formatear()
        procesa_argumento_observacion(parser=a,tarea_id=t.id)
    elif a.editar:
        t = Tarea(a.editar)
        t.editar(nombre=a.nombre,fecha_limite=a.fechalimite,estimacion=a.estimacion)
        procesa_argumento_observacion(parser=a,tarea_id=t.id)
    elif a.pausatodas:
        pausar_todo()
    elif a.tareas or not a.tareas:
        estados = None
        if a.filtroestado is None:
            estados = [CURSANDO,NUEVO,PAUSADO]
        tareas(proyectos=a.filtroproyecto,estados=estados,desde=alias_fechahora(a.desde),hasta=alias_fechahora(a.hasta))

def alias_fecha(alias,incluye_hora=False):
    fecha = None
    if alias == '' or alias == 'hoy':
        fecha = datetime.datetime.today().date()
    elif alias == 'ayer':
        fecha = datetime.datetime.today().date() - timedelta(1)
    else:
        try:
            fecha = datetime.datetime.strptime(alias,'%Y-%m-%d').date()
        except:
            fecha = None
    return time.mktime(fecha.timetuple())

def alias_fechahora(alias):
    fecha = None
    hoy = datetime.datetime.today()
    if alias == '' or alias == 'hoy':
        fecha_hora = datetime.datetime.combine(hoy,datetime.time())
    elif alias == 'ayer':
        fecha = hoy.date() - datetime.timedelta(1)
        fecha_hora = datetime.datetime.combine(fecha,datetime.time())
    else:
        try:
            spliteados = alias.split('-')
            hora    = 0
            minuto  = 0
            segundo = 0
            if len(spliteados) == 1:
                dia  = int(spliteados[0])
                mes  = hoy.month
                ano  = hoy.year
                fecha_hora = datetime.datetime(ano,mes,dia,hora,minuto,segundo)
            elif len(spliteados) == 2:
                dia  = int(spliteados[1])
                mes  = int(spliteados[0])
                ano = hoy.year
                fecha_hora = datetime.datetime(ano,mes,dia,hora,minuto,segundo)
            elif len(spliteados) == 3:
                parte_fecha_hora = alias.split(' ')
                if len(parte_fecha_hora) == 2:
                    parte_hora_min_seg = parte_fecha_hora[1].split(':')
                    if len(parte_hora_min_seg) == 2:
                        minuto = int(parte_hora_min_seg[1])
                        hora   = int(parte_hora_min_seg[0])
                    elif len(parte_hora_min_seg) == 3:
                        segundo = int(parte_hora_min_seg[2])
                        minuto  = int(parte_hora_min_seg[1])
                        hora    = int(parte_hora_min_seg[0])
                    dia  = int(parte_fecha_hora[0].split('-')[2])
                else:
                    dia  = int(spliteados[2])
                mes  = int(spliteados[1])
                ano  = int(spliteados[0])
                fecha_hora = datetime.datetime(ano,mes,dia,hora,minuto,segundo)
            else:
                fecha_hora = datetime.datetime.strptime(alias,'%Y-%m-%d %H:%M:%S')
        except:
            return None
    return (fecha_hora - datetime.datetime(1970,1,1)).total_seconds()

def procesa_argumento_observacion(parser, tarea_id=None,estado_del_arte_id=None):
     if parser.observacion:
         tipo_obs = None
         if parser.observacionriesgo:
             tipo_obs = OBS_RIESGO
         if parser.observaciontodo:
             tipo_obs = OBS_TODO
         if parser.observacionamenaza:
             tipo_obs = OBS_AMENAZA
         if parser.observacionnormal:
             tipo_obs = OBS_NORMAL
         if parser.observacionpasado:
             tipo_obs = OBS_PASADO
         o = Observacion()
         o.observacion=parser.observacion
         o.tarea_id = tarea_id
         o.tipo = tipo_obs
         o.crea()

if __name__ == '__main__':
    main()
