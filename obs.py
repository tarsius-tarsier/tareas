#!/usr/bin/env python
import tareas
import argparse

def listar(tipo=None,completado=False):
    for x in tareas.get_observaciones(tipo=tipo,completado=completado):
        print x.formatear_todo()

def terminar(id):
    o = tareas.Observacion(id)
    o.completa()

def main():
    a = argparse.ArgumentParser()
    tipos = a.add_mutually_exclusive_group()
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
    a.add_argument('-t','--terminar',type=int,help='termina')

    p = a.parse_args()
    if p.riesgos:
        listar(tipo=p.riesgos)
    elif p.amenazas:
        listar(tipo=p.amenazas)
    elif p.todo:
        listar(tipo=p.todo)
    elif p.normal:
        listar(tipo=p.normal)
    elif p.terminar:
        terminar(p.terminar)

if __name__ == '__main__':
    main()
