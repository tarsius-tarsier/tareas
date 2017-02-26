#!/usr/bin/env python
import tareas
import argparse

def listar(ids=None,tipo=None,completado=False,proyectos=None,nombres=None):
    return tareas.get_observaciones(tipo=tipo,
                                    completado=completado,
                                    ids=ids,
                                    nombres=nombres,
                                    proyectos=proyectos,
                                    ordenadas='prioridad desc')

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
    a.add_argument('-t','--termina',type=int,help='termina',action='append')
    a.add_argument('-tb','--terminabatch',action="store_true",help='termina en modo batch')
    a.add_argument('-Pb','--postponebatch',action="store_true",help='postpone en modo batch')
    a.add_argument('-fp','--filtroproyecto',type=int,action='append',help='filtro id proyecto')
    a.add_argument('-fo','--filtroobservacion',type=int,action='append',help='filtro id observacion')
    a.add_argument('-fn','--filtronombre',type=str,action='append',help='filtro nombre observacion')

    p = a.parse_args()
    if p.riesgos:
        riesgos = listar(ids=p.filtroobservacion,tipo=p.riesgos,proyectos=p.filtroproyecto,nombres=p.filtronombre)
        if p.maximaprioridad:
            o = tareas.Observacion(p.maximaprioridad)
            o.maxima_prioridad(entre=[r.id for r in riesgos])
        elif p.terminabatch:
            for r in riesgos:
                terminar([r.id],p.comentario)
        else:
            for r in riesgos:
                print r.formatear()

    elif p.amenazas:
        amenazas = listar(ids=p.filtroobservacion,tipo=p.amenazas,proyectos=p.filtroproyecto,nombres=p.filtronombre)
        if p.maximaprioridad:
            o = tareas.Observacion(p.maximaprioridad)
            o.maxima_prioridad(entre=[a.id for a in amenazas])
        elif p.terminabatch:
            for a in amenazas:
                terminar([a.id],p.comentario)
        else:
            for a in amenazas:
                print a.formatear()

    elif p.todo:
        todo = listar(ids=p.filtroobservacion,tipo=p.todo,proyectos=p.filtroproyecto,nombres=p.filtronombre)
        if p.maximaprioridad:
            o = tareas.Observacion(p.maximaprioridad)
            o.maxima_prioridad(entre=[t.id for t in todo])
        elif p.terminabatch:
            for t in todo:
                terminar([t.id],p.comentario)
        elif p.postponebatch:
            if p.motivo:
                for t in todo:
                    postponer([t.id],motivo=p.motivo)
        else:
            for t in todo:
                print t.formatear()
    elif p.pasado:
        pasadas = listar(ids=p.filtroobservacion,tipo=p.pasado,proyectos=p.filtroproyecto,nombres=p.filtronombre)
        if p.maximaprioridad:
            o = tareas.Observacion(p.maximaprioridad)
            o.maxima_prioridad(entre=[p.id for p in pasadas])
        elif p.terminabatch:
            for pa in pasadas:
                terminar([pa.id],p.comentario)
        else:
            for pa in pasadas:
                print pa.formatear()

    elif p.normal:
        normales = listar(ids=p.filtroobservacion,tipo=p.normal,proyectos=p.filtroproyecto,nombres=p.filtronombre)
        if p.maximaprioridad:
            o = tareas.Observacion(p.maximaprioridad)
            o.maxima_prioridad(entre=[n.id for n in normales])
        elif p.terminabatch:
            for n in normales:
                terminar([n.id],p.comentario)
        else:
            for n in normales:
                print n.formatear()
    elif p.termina:
        terminar(ids=p.terminar,comentario=p.comentario)
    elif p.subirprioridad:
        subir_prioridad(ids=p.subirprioridad)
    elif p.bajarprioridad:
        bajar_prioridad(ids=p.bajarprioridad)
    elif p.postponer:
        if p.motivo:
            postponer(ids=p.postponer,motivo=p.motivo)
    else:
        for o in listar(ids=p.filtroobservacion,proyectos=p.filtroproyecto,nombres=p.filtronombre):
            print o.formatear()

if __name__ == '__main__':
    main()
