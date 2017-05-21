from scapy.all import *
import os
import sys


# Recibe un string con la ip/url de destino y un ttl maximo del paquete (para que el algortimo termine)
def traceroute(destino, ttlMaximo):

    for i in range(1,ttlMaximo+1):
        # armo el paquete con el ttl incluido
        paquete = IP(dst=destino,ttl=i)/ICMP()
        # hago un echo request o ping para los pibes
        request = sr1(paquete)
        print request.src
        # veo si llego
        if request[ICMP].code != 0: # llego a destino
            print "Con ttl="+str(i)+" el paqete llego"
            break
        else:
            print "Con ttl="+str(i)+" el paquete no llego :("

if os.geteuid() != 0:
    print "Correlo con root chabon!"
    exit(1)

host = raw_input("Pone la ip/url:")
ttlMax = int(raw_input("Pone el ttl maximo:"))
traceroute(host, ttlMax)
