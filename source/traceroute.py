from scapy.all import *
import os, sys, time, csv

CANT_REP = 5
TYPE_TIMEEXCEDED = 11
LINEA_PAIS = 468
LINEA_REGION = 479
LINEA_CIUDAD = 484
LINEA_LATITUD = 501
LINEA_LONGITUD =506

def dameLinea(numLinea):
    return os.popen("head -n"+str(numLinea)+" dummy | tail -n1 | sed 's/<span>//g' | sed 's/<\/span>//g' | sed 's/\t//g'").read()[:-1]

# Recibe un string con la ip/url de destino y un ttl maximo del paquete (para que el algortimo termine)
def traceroute(destino, ttlMaximo, outfile):
    route = []
    if outfile:
        logger = csv.writer(open(outfile + ".csv", "wb"))
        logger.writerow(["orden","ip","avg(rtt)","pais","region","ciudad","latitud","longitud"])

    for i in range(1, ttlMaximo + 1):
        host = {}
        time_sum = 0
        num_rep = 0
        while num_rep < CANT_REP:
            # arma el paquete con el ttl incluido
            paquete = IP(dst=destino,ttl=i)/ICMP()
            # hago un echo request o ping para los pibes
            start_time = time.time()
            response = sr1(paquete)
            end_time = time.time()
            # analizo response
            if response[ICMP].type == TYPE_TIMEEXCEDED:
                # fue time exceded
                # guarda ip del host al que llego
                host['ip'] = response.src
                # se suma el rtt para promediar
                time_sum += end_time - start_time
                # aumenta contador
                num_rep += 1
        # se guarda el rtt promedio
        host['rtt'] = time_sum / CANT_REP
        route.append(host)

    i = 1
    for host in route:
        if host['ip'][:7] != "192.168":
            # si el equipo es externo traigo datos de geolocalizacion poniendo la ip
            os.system("wget -O dummy https://geoiptool.com/es/?ip="+host['ip'])
        else:
            # si es el router interno le digo a la pagina que me rastree
            os.system("wget -O dummy https://geoiptool.com/")
        pais = dameLinea(LINEA_PAIS)
        region = dameLinea(LINEA_REGION)
        ciudad = dameLinea(LINEA_CIUDAD)
        latitud = dameLinea(LINEA_LATITUD)
        longitud = dameLinea(LINEA_LONGITUD)
        if outfile:
            logger.writerow([i, host['ip'], host['rtt'],pais,region,ciudad,latitud,longitud])
        print host['ip'] + " -> " + str(host['rtt'])
        i += 1
    # borro el archivo que baje
    os.system("rm dummy*")

if os.geteuid() != 0:
    print "Correlo con root chabon!"
    exit(1)

host = raw_input("Pone la ip/url: ")
ttlMax = int(raw_input("Pone el ttl maximo: "))
outfile = raw_input("Pone el archivo de salida de logs (ENTER: sin log): ")
traceroute(host, ttlMax, outfile)
