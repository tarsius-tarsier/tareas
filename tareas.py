import sqlite3
import argparse
import time
import shutil
import os
from datetime import datetime

conexion = sqlite3.connect('tareas.db')
cursor   = conexion.cursor()
escritorio  = os.path.join(os.path.expanduser('~'),'Desktop')
ruta_archivos  = os.path.join(os.path.expanduser('~'),'workspace')

CURSANDO  = 'c'
TERMINADO = 't'
NUEVO     = 'n'
PAUSADO   = 'p'

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

def tareas(imprimir=True,proyectos=None,estados=None):
    select = 'select * from tarea ';
    restr = ''
    where = ''
    if proyectos is not None:
        restr = 'proyecto_id in ({}) '.format(','.join([str(x) for x in proyectos]))
        where = 'where '

    if estados is not None:
        o = ''
        if proyectos is not None:
            o = 'and '
        else:
            where = 'where '
        restr = '{}{}estado in ({}) '.format(restr,o,','.join(["'{}'".format(x) for x in estados]))

    cursor.execute('{}{}{} order by creada asc'.format(select,where,restr))
    r = cursor.fetchall()
    if imprimir:
        print encabezado_tarea()
    tareas = []
    for fila in r:
        t = Tarea(tupla=fila)
        if imprimir:
            print t.formatear()
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
    return time.mktime(datetime.strptime(fecha, '%Y-%m-%d %H:%M:%S').timetuple()) 

def convierte_desde_unix(unix):
    return datetime.fromtimestamp(int(unix))

class Tarea():
    def __init__(self,id=None,tupla=None,nombre=None,proyecto=None,estimacion=None,fecha_limite=None):
        self.id           = id
        self.nombre       = nombre
        self.proyecto_id  = proyecto
        self.estimacion   = estimacion
        self.fecha_limite = None
        fecha_limite_string = fecha_limite
        if fecha_limite_string is not None:
            self.fecha_limite = convierte_a_unix(fecha_limite_string)
        if id is not None:
            self.desde_db(id)
        if tupla is not None:
            self.desde_tupla(tupla)

    def eliminar(self,id):
        cursor.execute("delete from log where tarea_id=?",(id, ))
        cursor.execute("delete from lapso where tarea_id=?",(id, ))
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
        ahora = datetime.now()
        if self.fecha_limite is None:
            return 'i'
        fecha_limite = convierte_desde_unix(self.fecha_limite)
        diferencia = fecha_limite-ahora
        if self.terminada and self.estado == TERMINADO: 
            diferencia = fecha_limite - convierte_desde_unix(self.terminada)
        return '{}'.format(round((diferencia.total_seconds()/86400.0),1))

    def diferencia(self):
        estimadas = self.hh_estimadas
        hh = self.hh()
        if estimadas is None:
            estimadas = 0
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
        # cambia estado a c (cursando)
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

    def formatear(self,detalle=False):
        if self.id is None:
            return ''
        if detalle:
            termino = ''
            if self.estado == TERMINADO and self.terminada is not None:
                t = convierte_desde_unix(self.terminada)
                termino = 'ft:\t{}\n'.format(t)
            if self.fecha_limite is None:
                fl = ''
            else:
                fl = convierte_desde_unix(self.fecha_limite)
            return 'id:\t{}\npid:\t{}\nnombre:\t{}\nestado:\t{}\nhh:\t{}\nest:\t{}\ndif:\t{}\n{}fl:\t{}\nr:\t{}'.format(
                    self.id,
                    self.proyecto_id,
                    self.nombre,
                    self.estado,
                    self.hh(),
                    self.hh_estimadas,
                    self.diferencia(),
                    termino,
                    fl,
                    self.resta())
        else:
            return '{}\t{}\t{}\t{}\t{}\t{}\t{}'.format(self.id,self.proyecto_id,self.estado,self.hh(),self.diferencia(),self.resta(),self.nombre)

def pausar_todo():
    lista = tareas(imprimir=False)
    for t in lista:
        t.pausar()

def encabezado_proyecto():
    return 'id\tnombre'

def encabezado_tarea():
    return 'id\tpid\testado\thh\tdif\tr\ttarea'

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
    p.add_argument('-c','--cerrar',action='store_true',help='cierra todas las tareas')
    p.add_argument('-fe','--filtroestado',action='append',help='filtro estado')
    p.add_argument('-fp','--filtroproyecto',type=int,action='append',help='filtro proyecto')
    p.add_argument('-s','--editar',help='edita tarea')
    p.add_argument('-n','--nombre',help='nuevo nombre de tarea')
    p.add_argument('-de','--desde',help='desde')
    p.add_argument('-ha','--hasta',help='hasta')
    a = p.parse_args()
    if a.cerrar:
        pausar_todo()
    if a.archiva:
        t = Tarea()
        t.archivar(a.archiva)
    if a.elimina:
        t = Tarea()
        t.eliminar(a.elimina)
    if a.recupera:
        t = Tarea()
        t.recuperar(a.recupera)
    if a.iniciar:
        t = Tarea(a.iniciar)
        t.iniciar()
    if a.terminar:
        t = Tarea(a.terminar)
        t.terminar()
    if a.pausar:
        t = Tarea(a.pausar)
        t.pausar()
    if a.tareas:
        tareas(proyectos=a.filtroproyecto,estados=a.filtroestado)
    if a.horashombre:
        t = Tarea(a.horashombre)
        print t.hh(desde=convierte_a_unix(a.desde),hasta=convierte_a_unix(a.hasta))
    if a.ver:
        t = Tarea(a.ver)
        print t.formatear(detalle=True)
    if a.agrega:
        t = Tarea(nombre=a.agrega,proyecto=a.proyecto,estimacion=a.estimacion,fecha_limite=a.fechalimite)
        t.guardar()
        print t.formatear()
    if a.proyectos:
        proyectos()
    if a.editar:
        t = Tarea(a.editar)
        t.editar(nombre=a.nombre,fecha_limite=a.fechalimite,estimacion=a.estimacion)

if __name__ == '__main__':
    main()
