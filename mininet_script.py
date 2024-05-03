from mininet.net import Mininet
from mininet.topo import SingleSwitchTopo
from mininet.node import Host
from mininet.link import TCLink
from mininet.util import dumpNodeConnections

import time

def main():
    # Creamos una tología de red con un switch y dos hosts
    topo = SingleSwitchTopo(2)

    # Creamos una red Mininet con la topología creada, hosts normales y un link que nos
    # permita simular packet loss.
    net = Mininet(topo=topo, host=Host, link=TCLink)

    # Iniciamos la red
    net.start()
    dumpNodeConnections(net.hosts)
    # Obtenemos referencias a los hosts
    client = net.get('h1')
    server = net.get('h2')

    # Obtenemos el IP del servidor dentro de mininet
    server_ip = server.IP()

    # Iniciamos el servidor en el host del servidor (lo hacemos en el
    # background para poder pasar a la siguiente línea)
    server.cmd('python3 src/start-server.py -v -H localhost -p 3006 -s files/server_files -w > server_output.txt 2>&1 &')

    # Iniciamos el cliente en el host del cliente (lo hacemos en el
    # background para poder pasar a la siguiente línea)
    client.cmd(f'python3 src/upload.py -v -H {server_ip} -p 3006 -s files/upload_files -n batman.png -w > client_output.txt 2>&1 &')

    # Esperamos 20 segundos para que el cliente y el servidor terminen
    # Lo hacemos así porque ahora mismo nunca regresan esos programas,
    # por lo que no podemos hacer un net.wait() para esperar a que terminen
    time.sleep(10)

    # Stop Mininet
    net.stop()

if __name__ == '__main__':
    main()