from scapy.all import *
import os, sys, time, csv

CANT_REP = 5
TYPE_TIMEEXCEDED = 11

# Recibe un string con la ip/url de destino y un ttl maximo del paquete (para que el algortimo termine)
def traceroute(destino, ttlMaximo, outfile):
    route = []
    if outfile:
        logger = csv.writer(open(outfile + ".csv", "wb"))

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
        if outfile:
            logger.writerow([i, host['ip'], host['rtt']])
        print host['ip'] + " -> " + str(host['rtt'])
        i += 1

if os.geteuid() != 0:
    print "Correlo con root chabon!"
    exit(1)

host = raw_input("Pone la ip/url: ")
ttlMax = int(raw_input("Pone el ttl maximo: "))
outfile = raw_input("Pone el archivo de salida de logs (ENTER: sin log): ")
traceroute(host, ttlMax, outfile)
