from scapy.all import *
import os, sys, time, csv
import json, requests

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

# Recibe un string con la ip/url de destino y un ttl maximo del paquete (para que el algortimo termine)
def traceroute(destino, ttlMaximo, outfile):
    route = []
    if not outfile:
        outfile = "salida" + str(time.time())
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
                    print "========================REPITE IP================="
                    # fin = 1
                else:
                    print "contacto host: " + str(response.src)
                    if response[ICMP].type == TYPE_TIMEEXCEDED or response[ICMP].type == TYPE_LASTNODE:
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
        # si es de red interna le digo a la pagina que me rastree
        pais = ""
        region = ""
        ciudad = ""
        latitud = ""
        longitud = ""
        respok = 0
        intentos_geo = 0
        while not respok and intentos_geo < 10:
            response = requests.get("http://freegeoip.net/json/" + str(host['ip']))
            if response.status_code == 200:
                # parsea el json de respuesta de la api
                infoip = json.loads(response.content)
                # se guarda los datos necesarios
                pais = infoip['country_name'].encode('utf-8')
                region = infoip['region_name'].encode('utf-8')
                ciudad = infoip['city'].encode('utf-8')
                latitud = infoip['latitude']
                longitud = infoip['longitude']
                # setea que recibe los datos ok
                respok = 1
            intentos_geo += 1
        for rtt in host['tiempos']:
            logger.writerow([host['ttl'], host['ip'], rtt, pais, region, ciudad, latitud, longitud])

if os.geteuid() != 0:
    print "Correlo con root chabon!"
    exit(1)

if len(sys.argv) > 3:
    host = sys.argv[1]
    ttlMax = sys.argv[2]
    outfile = sys.argv[3]
else:
    host = raw_input("Pone la ip/url: ")
    ttlMax = int(raw_input("Pone el ttl maximo: "))
    outfile = raw_input("Pone el archivo de salida de logs: ")
traceroute(host, ttlMax, outfile)
