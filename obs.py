#!/usr/bin/env python
import tareas
import argparse

def listar(tipo=None,completado=False,proyectos=None):
    for x in tareas.get_observaciones(tipo=tipo,completado=completado,proyectos=proyectos):
        print x.formatear()

def terminar(id,comentario=None):
    o = tareas.Observacion(id)
    o.completa(comentario)

def postponer(id,motivo):
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
                       type=int,
                       help='postponer una observacion')
    a.add_argument( '-m',
                    '--motivo',
                     help='motivo por el cual se postpone')
    a.add_argument( '-c',
                    '--comentario',
                     help='comentario de termino')
    a.add_argument('-t','--terminar',type=int,help='termina')
    a.add_argument('-fp','--filtroproyecto',type=int,action='append',help='filtro proyecto')

    p = a.parse_args()
    if p.riesgos:
        listar(tipo=p.riesgos,proyectos=p.filtroproyecto)
    elif p.amenazas:
        listar(tipo=p.amenazas,proyectos=p.filtroproyecto)
    elif p.todo:
        listar(tipo=p.todo,proyectos=p.filtroproyecto)
    elif p.pasado:
        listar(tipo=p.pasado,proyectos=p.filtroproyecto)
    elif p.normal:
        listar(tipo=p.normal,proyectos=p.filtroproyecto)
    elif p.terminar:
        terminar(p.terminar,p.comentario)
    elif p.postponer:
        if p.motivo:
            postponer(id=p.postponer,motivo=p.motivo)

if __name__ == '__main__':
    main()
