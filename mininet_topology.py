from mininet.topo import Topo
from mininet.link import TCLink


class RedesTopo(Topo):
    "Topología para la red que usaremos en la presentación del TP1 de Redes"

    def __init__(self):
        "Creamos la topología"

        # Initialize topology
        Topo.__init__(self)
        # Agregamos hosts y switches
        server = self.addHost('server')
        client1 = self.addHost('client1')
        client2 = self.addHost('client2')
        client3 = self.addHost('client3')
        switch = self.addSwitch('s1')

        # Add links
        self.addLink(server, switch, cls=TCLink, loss=5)
        self.addLink(client1, switch, cls=TCLink, loss=5)
        self.addLink(client2, switch, cls=TCLink, loss=5)
        self.addLink(client3, switch, cls=TCLink, loss=5)


topos = {'redesTopo': (lambda: RedesTopo())}
