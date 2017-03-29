#!/usr/bin/env python
import tareas
import argparse

def listar(ids=None,
           e_ids=None,
           tipo=None,
           completada=False,
           tareas_id=None,
           tareas_nombre=None,
           incluye_completado=False,
           proyectos=None,
           proyectos_nombre=None,
           nombres=None):
    return tareas.get_observaciones(tipo=tipo,
                                    completado=completada,
                                    e_ids=e_ids,
                                    ids=ids,
                                    incluye_completado=incluye_completado,
                                    nombres=nombres,
                                    tareas_id=tareas_id,
                                    tareas_nombre=tareas_nombre,
                                    proyectos=proyectos,
                                    proyectos_nombre=proyectos_nombre,
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
    a.add_argument('-e',
                       '--elimina',
                       type=int,
                       help='elimina observacion')
    a.add_argument('-l',
                       '--incluyecompletado',
                       action='store_true',
                       help='incluye completados')
    a.add_argument('-s',
                       '--edita',
                       type=int,
                       help='edita una observacion')
    a.add_argument('-o',
                       '--observacion',
                       help='texto de observacion')
    a.add_argument('-tid',
                       '--tareaid',
                       type=int,
                       help='id de tarea')
    a.add_argument('-d',
                       '--completado',
                       type=bool,
                       help='activa o desactiva observacion')
    a.add_argument('-i',
                       '--prioridad',
                       type=int,
                       help='define prioridad de observacion')
    a.add_argument('-I',
                       '--tipo',
                       type=int,
                       help='cambia el tipo de observacion')
    a.add_argument('-mp',
                       '--maximaprioridad',
                       type=int,
                       help='define maxima prioridad')
    a.add_argument('-ip',
                       '--minimaprioridad',
                       type=int,
                       help='define minma prioridad')
    a.add_argument( '-m',
                    '--motivo',
                     help='motivo por el cual se postpone')
    a.add_argument( '-c',
                    '--comentario',
                     help='comentario de termino')
    a.add_argument( '-C',
                    '--completada',
                    action='store_true',
                    help='muestra las tareas completadas')
    a.add_argument('-Pb','--postponebatch',action="store_true",help='postpone en modo batch')
    a.add_argument('-eo','--exceptoobservacion',type=int,action='append',help='excepto id observacion')
    a.add_argument('-fn','--filtronombre',type=str,action='append',help='filtro nombre observacion')
    a.add_argument('-fo','--filtroobservacion',type=int,action='append',help='filtro id observacion')
    a.add_argument('-fp','--filtroproyecto',type=int,action='append',help='filtro id proyecto')
    a.add_argument('-fpn','--filtronombreproyecto',action='append',help='filtro nombre proyecto')
    a.add_argument('-ft','--filtrotarea',type=str,action='append',help='filtro nombre observacion')
    a.add_argument('-ftn','--filtronombretarea',action='append',help='filtro nombre tarea')
    a.add_argument('-t','--termina',type=int,help='termina',action='append')
    a.add_argument('-tb','--terminabatch',action="store_true",help='termina en modo batch')

    p = a.parse_args()

    if p.termina:
        terminar(ids=p.termina,comentario=p.comentario)
    elif p.edita:
        o = tareas.Observacion(id=p.edita)
        o.edita(p.observacion,p.tareaid,p.completado,p.prioridad,p.tipo)
    elif p.elimina:
        o = tareas.Observacion(id=p.elimina)
        o.elimina()
    elif p.subirprioridad:
        subir_prioridad(ids=p.subirprioridad)
    elif p.bajarprioridad:
        bajar_prioridad(ids=p.bajarprioridad)
    elif p.postponer:
        if p.motivo:
            postponer(ids=p.postponer,motivo=p.motivo)
    else:
        tipo = None
        if p.riesgos:
            tipo = tareas.OBS_RIESGO
        if p.amenazas:
            tipo = tareas.OBS_AMENAZA
        if p.normal:
            tipo = tareas.OBS_NORMAL
        if p.pasado:
            tipo = tareas.OBS_PASADO
        if p.todo:
            tipo = tareas.OBS_TODO

        observaciones = listar(e_ids=p.exceptoobservacion,
                               ids=p.filtroobservacion,
                               completada=p.completada,
                               incluye_completado=p.incluyecompletado,
                               tipo=tipo,
                               tareas_id=p.filtrotarea,
                               tareas_nombre=p.filtronombretarea,
                               proyectos=p.filtroproyecto,
                               proyectos_nombre=p.filtronombreproyecto,
                               nombres=p.filtronombre)

        if p.maximaprioridad:
            o = tareas.Observacion(p.maximaprioridad)
            o.maxima_prioridad(entre=[obs.id for obs in observaciones])
        elif p.minimaprioridad:
            o = tareas.Observacion(p.minimaprioridad)
            o.minima_prioridad(entre=[obs.id for obs in observaciones])
        else:
            for obs in observaciones:
                if p.terminabatch:
                    terminar([obs.id],p.comentario)
                elif obs.tipo == tareas.OBS_TODO and p.postponebatch and p.motivo:
                    postponer([obs.id],motivo=p.motivo)
                else:
                    print obs.formatear()

if __name__ == '__main__':
    main()
