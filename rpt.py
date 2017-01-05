from matplotlib import pyplot as plt
import argparse
import tareas
import datetime
import time

def histograma(dias=None,desde=None,hasta=None,archivo='reporte.pdf',proyectos=None):
    """ histograma de hh en periodo por dia """
    if hasta is None:
        hasta = datetime.datetime.today().date()
    if desde is None:
        if dias is None:
            dias = 7
        desde = hasta - datetime.timedelta(dias) 
    else:
        dias = (hasta - desde).days

    fechas  = []
    horas   = []
    for x in range(0,dias):
        fechas.append(hasta - datetime.timedelta(days=x))
        horas.append(hh((hasta - datetime.timedelta(days=x)),proyectos=proyectos))
    plt.gcf().subplots_adjust(bottom=0.25)
    plt.title(u'HH por dia')
    plt.xlabel(u'Dias')
    plt.ylabel('HH')
    plt.bar(fechas,horas)
    plt.xticks(fechas, fechas, rotation=70)
    plt.savefig(archivo)

def hh(desde,delta=1,proyectos=None):
    total = 0
    de = time.mktime(desde.timetuple())
    ha = time.mktime((desde+datetime.timedelta(delta)).timetuple())
    for t in tareas.tareas(imprimir=False,desde=de,hasta=ha,proyectos=proyectos):
        total = t.hh(desde=de,hasta=ha) + total
    return total

def main():
    a = argparse.ArgumentParser()
    a.add_argument('-i','--histograma',action='store_true',help='histograma de tareas')
    a.add_argument('-d','--dias',type=int)
    a.add_argument('-a','--archivo')
    a.add_argument('-fp','--filtroproyecto',type=int,action='append',help='filtro proyecto')
    a.add_argument('-de','--desde',help='desde')
    a.add_argument('-ha','--hasta',help='hasta')
    p = a.parse_args()
    if p.histograma:
        histograma(desde=p.desde,hasta=p.hasta,dias=p.dias,archivo=p.archivo,proyectos=p.filtroproyecto)

if __name__ == '__main__':
    main()
