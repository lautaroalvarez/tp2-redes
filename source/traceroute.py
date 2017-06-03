from scapy.all import *
import os, sys, time, csv
import json, requests
import numpy as np

CANT_REP = 50
MAX_INTENTOS = 3
TIME_LIMIT = 3
NODES_LIMIT = 30
TYPE_TIMEEXCEDED = 11
TYPE_LASTNODE = 0

# Recibe un string con la ip/url de destino y un archivo de salida
class traceroute():
    def __init__(self, destino, namefile):
        if not namefile:
            namefile = str(time.time())
        self.namefile = namefile
        self.destino = destino
        self.route = []
        self.numRep = 0
        self.numIntento = 0

    def iniciar(self):
        self.loggerRoute = csv.writer(open(self.namefile + "_route.csv", "wb"))
        self.loggerRoute.writerow(["ttl","ip","rtt","pais","region","ciudad","latitud","longitud"])
        self.ttlActual = 1
        fin_camino = False
        while not fin_camino and self.ttlActual < NODES_LIMIT:
            host = {}
            host['tiempos'] = []
            host['ttl'] = self.ttlActual
            self.numRep = 0
            numIntento = 0
            while self.numRep < CANT_REP and numIntento < MAX_INTENTOS:
                self.actualizarVistaProceso()
                # arma el paquete con el ttl incluido
                paquete = IP(dst=self.destino,ttl=self.ttlActual)/ICMP()
                # hago un echo request o ping para los pibes
                start_time = time.time()
                response = sr1(paquete, timeout=TIME_LIMIT)
                end_time = time.time()
                numIntento += 1
                if response:
                    # analizo response
                    if response[ICMP].type == TYPE_TIMEEXCEDED or response[ICMP].type == TYPE_LASTNODE:
                        # guarda ip del host al que llego
                        host['ip'] = response.src
                        # guarda el tiempo obtenido en el host
                        host['tiempos'].append(end_time - start_time)
                        # aumenta contador
                        self.numRep += 1
                        # reseteamos el numero de intentos
                        numIntento = 0
                    # chequeamos si es el nodo de destino
                    if response[ICMP].type == TYPE_LASTNODE:
                        print "PASA POR SALIDA"
                        fin_camino = True
            if len(host['tiempos']) > 0:
                last_ip = host['ip']
                self.route.append(host)
            self.ttlActual += 1

    def buscarIps(self):
        for host in self.route:
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
            # guarda en csv la salida
            for rtt in host['tiempos']:
                self.loggerRoute.writerow([host['ttl'], host['ip'], rtt, pais, region, ciudad, latitud, longitud])

    def estadoDesdeCsv(self, namefile):
        self.route = []
        self.namefile = namefile
        with open(self.namefile + '_route.csv', 'rb') as archivocsv:
            lector = csv.reader(archivocsv)
            self.ttlActual = -1
            ip_actual = -1
            primera_linea = 1
            host = {}
            for linea in lector:
                if primera_linea:
                    primera_linea = 0
                else:
                    if self.ttlActual != linea[0]:
                        if self.ttlActual > 0:
                            self.route.append(host)
                        self.ttlActual = linea[0]
                        host = {}
                        host['tiempos'] = []
                        host['ttl'] = self.ttlActual
                        host['ip'] = linea[1]
                    host['tiempos'].append(float(linea[2]))
            self.route.append(host)
            self.actualizarVistaProceso()

    def actualizarVistaProceso(self):
        os.system('clear')
        print "-------------TRACEROUTE-------------"
        print "Destino:       " + self.destino
        print "TTL actual:    " + str(self.ttlActual)
        print "Num captura:   " + str(self.numRep)
        print "------------------------------------"
        print ""
        for host in self.route:
            print str(host['ttl']) + " -> " + host['ip'] + " - " + str(promediarRtts(host['tiempos']))
        print ""

    def calcularOutliers(self):
        arrayIP_RTT = []
        # guarda rtt por salto
        rtt_ultimo_nodo = 0
        for host in self.route:
            rtt_promedio = promediarRtts(host['tiempos'])
            arrayIP_RTT.append((host['ip'], rtt_promedio - rtt_ultimo_nodo))
            rtt_ultimo_nodo = rtt_promedio

        # paso 0
        cantidad_nodos = len(arrayIP_RTT)
        # paso 1
        arrayIP_RTT_sorted = sorted(arrayIP_RTT,key=lambda x: x[1])
        candidatoMin = arrayIP_RTT_sorted[0]
        candidatoMax = arrayIP_RTT_sorted[len(arrayIP_RTT_sorted)-1]
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
        thompson = raw_input("Dame el thompson modificado con n="+str(cantidad_nodos))
        # paso 7
        valorCritico = float(thompson) * stdev
        print valorCritico
        # paso 8
        if valorCritico < masSospechoso:
            print "Para llegar a la ip "+(candidatoMin[0] if mayor else candidatoMax[0])+" hay un salto intercontinental"
        else:
            print "No hay salto intercontinental"

def promediarRtts(arregloRtt):
    return np.mean(np.array(arregloRtt))

if os.geteuid() != 0:
    print "Correlo con root chabon!"
    exit(1)

def main():
    if len(sys.argv) < 2:
        print "-----TRACEROUTE-----"
        print "Modos:"
        print "1 -> Capturar:"
        print "    Parametros:"
        print "        1. Host"
        print "        2. Nombre de salida"
        print "2 -> Usar archivo de entrada"
        print "        1. Nombre de entrada"
        print ""
        print "Ejemplos:"
        print "   traceroute.py 1 cambridge.ac.uk cambridge"
        print "   traceroute.py 2 cambridge"
        return

    if sys.argv[1] == '1':
        if len(sys.argv) > 3:
            host = sys.argv[2]
            namefile = sys.argv[3]
        else:
            host = raw_input("Pone la ip/url: ")
            namefile = raw_input("Pone el nombre del archivo de salida de logs: ")
        tr = traceroute(host, namefile)
        tr.iniciar()
        tr.buscarIps()
    else:
        if len(sys.argv) > 2:
            namefile = sys.argv[2]
        else:
            namefile = raw_input("Pone el nombre del archivo de entrada: ")
        tr = traceroute('', '')
        tr.estadoDesdeCsv(namefile)
        tr.calcularOutliers()

main()
