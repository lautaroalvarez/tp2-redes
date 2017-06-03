import sys, csv
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

LISTA_TAU = [0, 0, 0, 1.1511, 1.4250, 1.5712, 1.6563, 1.7110, 1.7491, 1.7770, 1.7984, 1.8153, 1.8290, 1.8403, 1.8498, 1.8579, 1.8649, 1.8710, 1.8764, 1.8811, 1.8853, 1.8891, 1.8926, 1.8957, 1.8985, 1.9011, 1.9035, 1.9057, 1.9078, 1.9096, 1.9114]

class graficador():
    def __init__(self, namefile):
        self.namefile = namefile
        self.route = []
        self.importarRoute()

    def importarRoute(self):
        with open(self.namefile + '.csv', 'rb') as archivocsv:
            lector = csv.reader(archivocsv)
            ttlActual = -1
            ip_actual = -1
            primera_linea = 1
            ultimo_rtt = 0
            host = {}
            for linea in lector:
                if primera_linea:
                    primera_linea = 0
                else:
                    if ttlActual != int(linea[0]):
                        if ttlActual > 0:
                            host['rtt_promedio'] = promediarRtts(host['tiempos'])
                            host['rtt_salto'] = host['rtt_promedio'] - ultimo_rtt
                            ultimo_rtt = host['rtt_promedio']
                            self.route.append(host)
                        ttlActual = int(linea[0])
                        host = {}
                        host['tiempos'] = []
                        host['ttl'] = ttlActual
                        host['ip'] = linea[1]
                        host['pais'] = linea[3]
                        host['region'] = linea[4]
                        host['ciudad'] = linea[5]
                        host['latitud'] = linea[6]
                        host['longitud'] = linea[7]
                    host['tiempos'].append(float(linea[2]))
            host['rtt_promedio'] = promediarRtts(host['tiempos'])
            host['rtt_salto'] = host['rtt_promedio'] - ultimo_rtt
            ultimo_rtt = host['rtt_promedio']
            self.route.append(host)

    def gRttEntraSaltos(self):
        ips = []
        rtts = []
        for host in self.route:
            ips.append(host['ip'])
            rtts.append(host['rtt_salto'])

        fig, ax = plt.subplots()
        ax.set_xlim([min(rtts) - 0.03 * abs(max(rtts)-min(rtts)), max(rtts) + 0.03 * abs(max(rtts)-min(rtts))])
        ax.set_ylim([-1, len(ips)])
        ax.barh(np.arange(len(ips)), rtts, align='center')
        ax.set_yticks(np.arange(len(ips)))
        ax.set_yticklabels(ips)
        ax.invert_yaxis()
        ax.set_xlabel('RTT promedio del salto')
        ax.set_title('Nodos de la ruta obtenida')
        sns.set_style("darkgrid")
        plt.show()

    def gRttVsCimbala(self):
        ips = []
        rtts = []
        for host in self.route:
            ips.append(host['ip'])
            rtts.append(host['rtt_salto'])
        promedio = np.mean(np.array(rtts))
        std = np.std(np.array(rtts))
        values = []
        for rtt in rtts:
            values.append(abs(rtt - promedio) / std)

        fig, ax = plt.subplots()
        ax.barh(np.arange(len(ips)), values, align='center')
        ax.set_yticks(np.arange(len(ips)))
        ax.set_yticklabels(ips)
        ax.invert_yaxis()
        ax.set_xlabel('RTT promedio del salto')
        ax.set_title('Nodos de la ruta obtenida')
        sns.set_style("darkgrid")
        ax.plot([LISTA_TAU[len(ips)], LISTA_TAU[len(ips)]], [-1, len(ips)], "r--")
        plt.show()

def promediarRtts(lista):
    listaOrdenada = np.sort(np.array(lista))
    listaOrdenada = np.delete(listaOrdenada, [0, listaOrdenada.shape[0]-1])
    return np.mean(listaOrdenada)

def main():
    if len(sys.argv) < 3:
        print "PARAMETROS:"
        print "    python graficadores.py ARCHIVO_DE_ENTRADA TIPO_GRAFICO"
        print "TIPOS:"
        print "    1. RTT entre saltos"
        return

    graph = graficador(sys.argv[1])
    if sys.argv[2] == '1':
        graph.gRttEntraSaltos()
    else:
        graph.gRttVsCimbala()

if __name__ == "__main__":
    main()
