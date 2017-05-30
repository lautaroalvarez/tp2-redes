from scapy.all import *
import os, sys, time, csv, geoip2.webservice

CANT_REP = 5
MAX_INTENTOS = 5
TIME_LIMIT = 3
TYPE_TIMEEXCEDED = 11
TYPE_LASTNODE = 0
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
        logger.writerow(["orden","ip","num_rep","pais","region","ciudad","latitud","longitud"])

    ttlActual = 1
    fin = 0
    last_ip = ''
    while ttlActual <= ttlMaximo and not fin:
        host = {}
        host['tiempos'] = []
        host['ttl'] = ttlActual
        num_rep = 0
        num_intentos = 0
        while num_rep < CANT_REP and num_intentos < MAX_INTENTOS and not fin:
            print "-----------------------"
            print "----ttl: " + str(ttlActual) + " - num_rep: " + str(num_rep) + " - num_intentos: " + str(num_intentos)
            # arma el paquete con el ttl incluido
            paquete = IP(dst=destino,ttl=ttlActual)/ICMP()
            # hago un echo request o ping para los pibes
            start_time = time.time()
            response = sr1(paquete, timeout=TIME_LIMIT)
            end_time = time.time()
            num_intentos += 1
            if response:
                # analizo response
                # si la ip es la misma que un ttl anterior, entonces ya llegue al final
                if last_ip == response.src:
                    print "========================REPITE LAST IP!!========================="
                    fin = 1
                else:
                    print "type: " + str(response[ICMP].type)
                    print "host: " + str(response.src)
                    if response[ICMP].type == TYPE_TIMEEXCEDED or response[ICMP].type == TYPE_LASTNODE:
                        print "se guarda ok"
                        # fue time exceded
                        # guarda ip del host al que llego
                        host['ip'] = response.src
                        # guarda el tiempo obtenido en el host
                        host['tiempos'].append(end_time - start_time)
                        # aumenta contador
                        num_rep += 1
                        #reseteamos el numero de intentos
                        num_intentos = 0
        if len(host['tiempos']) > 0:
            last_ip = host['ip']
            route.append(host)
        ttlActual += 1

    for host in route:
        if host['ip'][:7] == "192.168" or host['ip'][:3] == "10." or host['ip'][:7] == "192.16." or host['ip'][:7] == "169.254":
            # si es de red interna le digo a la pagina que me rastree
            os.system("wget -O dummy https://geoiptool.com/")
        else:
            # si el equipo es externo traigo datos de geolocalizacion poniendo la ip
            os.system("wget -O dummy https://geoiptool.com/es/?ip="+host['ip'])
        pais = dameLinea(LINEA_PAIS)
        region = dameLinea(LINEA_REGION)
        ciudad = dameLinea(LINEA_CIUDAD)
        latitud = dameLinea(LINEA_LATITUD)
        longitud = dameLinea(LINEA_LONGITUD)
        if outfile:
            for rtt in host['tiempos']:
                logger.writerow([host['ttl'], host['ip'], rtt, pais, region, ciudad, latitud, longitud])
    # borro el archivo que baje
    os.system("rm dummy*")

if os.geteuid() != 0:
    print "Correlo con root chabon!"
    exit(1)

host = raw_input("Pone la ip/url: ")
ttlMax = int(raw_input("Pone el ttl maximo: "))
outfile = raw_input("Pone el archivo de salida de logs (ENTER: sin log): ")
traceroute(host, ttlMax, outfile)
