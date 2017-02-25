#!/usr/bin/env python
import tareas
import argparse

def listar(tipo=None,completado=False,proyectos=None):
    return tareas.get_observaciones(tipo=tipo,completado=completado,proyectos=proyectos,ordenadas='prioridad desc')

def subir_prioridad(ids):
    for id in ids:
        o = tareas.Observacion(id)
        o.sube_prioridad()

def bajar_prioridad(ids):
    for id in ids:
        o = tareas.Observacion(id)
        o.baja_prioridad()

def terminar(ids,comentario=None):
    for id in ids:
        o = tareas.Observacion(id)
        o.completa(comentario)

def postponer(ids,motivo):
    for id in ids:
        o = tareas.Observacion(id)
        o.postponer(motivo)

def main():
    a = argparse.ArgumentParser()
    tipos = a.add_mutually_exclusive_group()
    tipos.add_argument('-p', '--pasado',
                       action='store_const',
                       const=tareas.OBS_PASADO,
                       help='lista observaciones pasado')
    tipos.add_argument('-n', '--normal',
                       action='store_const',
                       const=tareas.OBS_NORMAL,
                       help='lista observaciones normales')
    tipos.add_argument('-a', '--amenazas',
                       action='store_const',
                       const=tareas.OBS_AMENAZA,
                       help='lista amenazas')
    tipos.add_argument('-r',
                       '--riesgos',
                       action='store_const',
                       const=tareas.OBS_RIESGO,
                       help='lista riesgos')
    tipos.add_argument('-T',
                       '--todo',
                       action='store_const',
                       const=tareas.OBS_TODO,
                       help='lista cosas por hacer')
    tipos.add_argument('-P',
                       '--postponer',
                       action='append',
                       type=int,
                       help='postponer una observacion')
    a.add_argument('-bp',
                       '--bajarprioridad',
                       action='append',
                       type=int,
                       help='baja la prioridad de observacion')
    a.add_argument('-sp',
                       '--subirprioridad',
                       action='append',
                       type=int,
                       help='sube la prioridad de observacion')
    a.add_argument('-mp',
                       '--maximaprioridad',
                       type=int,
                       help='define maxima prioridad')
    a.add_argument( '-m',
                    '--motivo',
                     help='motivo por el cual se postpone')
    a.add_argument( '-c',
                    '--comentario',
                     help='comentario de termino')
    a.add_argument('-t','--terminar',type=int,help='termina',action='append')
    a.add_argument('-fp','--filtroproyecto',type=int,action='append',help='filtro proyecto')

    p = a.parse_args()
    if p.riesgos:
        riesgos = listar(tipo=p.riesgos,proyectos=p.filtroproyecto)
        if p.maximaprioridad:
            o = tareas.Observacion(p.maximaprioridad)
            o.maxima_prioridad(entre=[r.id for r in riesgos])
        else:
            for r in riesgos:
                print r.formatear()

    elif p.amenazas:
        amenazas = listar(tipo=p.amenazas,proyectos=p.filtroproyecto)
        if p.maximaprioridad:
            o = tareas.Observacion(p.maximaprioridad)
            o.maxima_prioridad(entre=[a.id for a in amenazas])
        else:
            for a in amenazas:
                print a.formatear()

    elif p.todo:
        todo = listar(tipo=p.todo,proyectos=p.filtroproyecto)
        if p.maximaprioridad:
            o = tareas.Observacion(p.maximaprioridad)
            o.maxima_prioridad(entre=[t.id for t in todo])
        else:
            for t in todo:
                print t.formatear()
    elif p.pasado:
        pasadas = listar(tipo=p.pasado,proyectos=p.filtroproyecto)
        if p.maximaprioridad:
            o = tareas.Observacion(p.maximaprioridad)
            o.maxima_prioridad(entre=[p.id for p in pasadas])
        else:
            for p in pasadas:
                print p.formatear()

    elif p.normal:
        normales = listar(tipo=p.normal,proyectos=p.filtroproyecto)
        if p.maximaprioridad:
            o = tareas.Observacion(p.maximaprioridad)
            o.maxima_prioridad(entre=[n.id for n in normales])
        else:
            for n in normales:
                print n.formatear()

    elif p.terminar:
        terminar(ids=p.terminar,comentario=p.comentario)
    elif p.subirprioridad:
        subir_prioridad(ids=p.subirprioridad)
    elif p.bajarprioridad:
        bajar_prioridad(ids=p.bajarprioridad)
    elif p.postponer:
        if p.motivo:
            postponer(ids=p.postponer,motivo=p.motivo)

if __name__ == '__main__':
    main()
