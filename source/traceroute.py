from scapy.all import *
import os, sys, time, csv
import json, requests
import numpy as np

CANT_REP = 3
MAX_INTENTOS = 2
TIME_LIMIT = 3
TYPE_TIMEEXCEDED = 11
TYPE_LASTNODE = 0

# Recibe un string con la ip/url de destino y un ttl maximo del paquete (para que el algortimo termine)
def traceroute(destino, outfile):
    route = []
    if not outfile:
        outfile = "salida" + str(time.time())
    logger = csv.writer(open(outfile + ".csv", "wb"))
    logger.writerow(["orden","ip","num_rep","pais","region","ciudad","latitud","longitud","tiempo"])

    ttlActual = 1
    fin_camino = 0
    while not fin_camino:
        host = {}
        host['tiempos'] = []
        host['ttl'] = ttlActual
        num_rep = 0
        num_intentos = 0
        while num_rep < CANT_REP and num_intentos < MAX_INTENTOS:
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
                if response[ICMP].type == TYPE_TIMEEXCEDED or response[ICMP].type == TYPE_LASTNODE:
                    # guarda ip del host al que llego
                    host['ip'] = response.src
                    # guarda el tiempo obtenido en el host
                    host['tiempos'].append(end_time - start_time)
                    # aumenta contador
                    num_rep += 1
                    # reseteamos el numero de intentos
                    num_intentos = 0
                # chequeamos si es el nodo de destino
                if response[ICMP].type == TYPE_LASTNODE:
                    fin_camino = 1
        if len(host['tiempos']) > 0:
            last_ip = host['ip']
            route.append(host)
        ttlActual += 1

    ej1 = True
    arrayIP_RTT = []
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
        if ej1:
            for rtt in host['tiempos']:
                logger.writerow([host['ttl'], host['ip'], rtt, pais, region, ciudad, latitud, longitud])
        else:
            tiempos = np.array(host['tiempos'])
            arrayIP_RTT.append((host['ip'],np.mean(tiempos)))

    if not ej1: # cimbala
        print arrayIP_RTT
        for i in range(1,len(arrayIP_RTT)): # calculo cuanto tardo en ese tramo
            arrayIP_RTT[i] = (arrayIP_RTT[i][0],arrayIP_RTT[i][1]-arrayIP_RTT[i-1][1])
        # paso 0
        cantidad = len(arrayIP_RTT)
        print cantidad
        # paso 1
        arrayIP_RTT_sorted = sorted(arrayIP_RTT,key=lambda x: x[1])
        candidatoMin = arrayIP_RTT_sorted[0]
        candidatoMax = arrayIP_RTT_sorted[len(arrayIP_RTT_sorted)-1]
        print candidatoMin
        print candidatoMax
        # paso 2
        np_rtt = []
        for par in arrayIP_RTT:
            rtt = par[1]
            np_rtt.append(rtt)
        np_rtt = np.array(np_rtt)
        media = np.mean(np_rtt)
        stdev = np.std(np_rtt)
        print media
        print stdev
        # paso 3
        desviacion_menorRTT = abs(candidatoMin[1]-media)
        # paso 4
        desviacion_mayorRTT = abs(candidatoMax[1]-media)
        # paso 5
        mayor = True
        if desviacion_mayorRTT < desviacion_menorRTT: # manganeta para tener cual es la ip a la hora de reportarla
            masSospechoso = desviacion_menorRTT
            mayor = False
        else:
            masSospechoso = desviacion_mayorRTT
        print masSospechoso
        # paso 6
        # TODO: hardcodear la tabla o calcularla si estamos con tiempos
        thompson = raw_input("Dame el thompson modificado con n="+str(cantidad))
        # paso 7
        valorCritico = thompson*stdev
        print valorCritico
        # paso 8
        if valorCritico < masSospechoso:
            print "Para llegar a la ip "+(candidatoMin[0] if mayor else candidatoMax[0])+" hay un salto intercontinental"

if os.geteuid() != 0:
    print "Correlo con root chabon!"
    exit(1)

if len(sys.argv) > 2:
    host = sys.argv[1]
    outfile = sys.argv[2]
else:
    host = raw_input("Pone la ip/url: ")
    outfile = raw_input("Pone el archivo de salida de logs: ")

traceroute(host, outfile)
