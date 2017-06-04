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
            ips.append(host['ip'] + " [ttl: " + str(host['ttl']) + "]")
            rtts.append(host['rtt_salto'])

        fig, ax = plt.subplots()
        ax.set_xlim([min(rtts) - 0.03 * abs(max(rtts)-min(rtts)), max(rtts) + 0.03 * abs(max(rtts)-min(rtts))])
        ax.set_ylim([-1, len(ips)])
        ax.barh(np.arange(len(ips)), rtts, align='center')
        ax.set_yticks(np.arange(len(ips)))
        ax.set_yticklabels(ips, fontsize=17)
        ax.invert_yaxis()
        ax.set_xlabel('RTT promedio del salto', fontsize=14)
        ax.set_title('Nodos de la ruta obtenida', fontsize=16)
        sns.set_style("darkgrid")
        box = ax.get_position()
        ax.set_position([0.35, box.y0, box.width - 0.15, box.height])
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

    def gRttVsCimbalaRecursivo(self):
        rtts = []
        rtt_ultimo_nodo = 0
        # calcula rtt por salto y los agrega a una lista para calcular promedio y std
        for host in self.route:
            host['es_salto'] = False
            rtt_promedio = promediarRtts(host['tiempos'])
            host['rtt_salto'] = rtt_promedio - rtt_ultimo_nodo
            rtt_ultimo_nodo = rtt_promedio
            rtts.append((host['ip'], host['rtt_salto']))

        # ordena por rtt de salto
        rtts = sorted(rtts, key=lambda x: x[1])

        ultimo_tau = 0
        promedio = 0
        std = 0
        hay_outlier = True
        while hay_outlier:
            hay_outlier = False
            # calcula promedio y std
            np_rtt = []
            for par in rtts:
                rtt = par[1]
                np_rtt.append(rtt)
            np_rtt = np.array(np_rtt)
            promedio = np.mean(np_rtt)
            std = np.std(np_rtt)
            # tomamos el rtt mas alto (candidato)
            candidato = rtts[-1]
            # recorre los nodos y verifica si son outliers
            i = 0
            while i < len(self.route) and self.route[i]['ip'] != candidato[0]:
                i += 1
            if i < len(self.route):
                value = abs(self.route[i]['rtt_salto'] - promedio) / std
                ultimo_tau = LISTA_TAU[len(rtts)]
                if value > ultimo_tau:
                    self.route[i]['valor'] = value
                    self.route[i]['es_salto'] = True
                    rtts.pop()
                    hay_outlier = True

        ips = []
        values = []
        colors = []
        for host in self.route:
            # guardo ip
            ips.append(host['ip'])
            # seteo color (si es negativo o positivo)
            if host['rtt_salto'] < 0:
                colors.append('#8fb2de')
            else:
                colors.append('#1c59a5')
            # guardo valor
            if host['es_salto']:
                values.append(host['valor'])
            else:
                values.append(abs(host['rtt_salto'] - promedio) / std)

        fig, ax = plt.subplots()
        ax.barh(np.arange(len(ips)), values, align='center', color=colors)
        ax.set_yticks(np.arange(len(ips)))
        ax.set_yticklabels(ips, fontsize=17)
        ax.invert_yaxis()
        ax.set_xlabel('Pone aca algo copado', fontsize=14)
        ax.set_title('aca otras cosas', fontsize=15)
        sns.set_style("darkgrid")
        ax.plot([ultimo_tau, ultimo_tau], [-1, len(ips)], "r--")
        box = ax.get_position()
        ax.set_position([0.25, box.y0, box.width - 0.05, box.height])
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
        print "    2. RTT entre saltos VS desviacion y tau"
        print "    3. RTT entre saltos VS desviacion y tau RECURSIVO"
        return

    graph = graficador(sys.argv[1])
    if sys.argv[2] == '1':
        graph.gRttEntraSaltos()
    elif sys.argv[2] == '2':
        graph.gRttVsCimbala()
    elif sys.argv[2] == '3':
        graph.gRttVsCimbalaRecursivo()

if __name__ == "__main__":
    main()
