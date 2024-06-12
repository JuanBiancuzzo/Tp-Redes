import json

from mininet.topo import Topo
from mininet.link import TCLink


class RedesTopo(Topo):
    "Topología para la red que usaremos en la presentación del TP2 de Redes"

    def __init__(self):
        "Creamos la topología"
        with open("config.json", "r") as jsonFile:
            data = json.load(jsonFile)

        cantSwitches = data["cantSwitches"]
        posFirewall = data["firewallSwitch"]

        if posFirewall > cantSwitches or posFirewall <= 0:
            print("No hay firewall")

        Topo.__init__(self)

        # Agregamos hosts
        cliente1 = self.addHost('cliente1')
        cliente2 = self.addHost('cliente2')
        cliente3 = self.addHost('cliente3')
        cliente4 = self.addHost('cliente4')

        # Agregamos switches
        switches = []
        for i in range(cantSwitches):
            if i != posFirewall - 1:
                switches.append(self.addSwitch(f"switch{i + 1}", stp = True))
                continue

            switches.append(self.addSwitch(f"firewall{i + 1}", stp = True))
            print("Se creo el firewall")

        # Agregamos links
        for i in range(cantSwitches - 1):
            self.addLink(switches[i], switches[i + 1], cls=TCLink)

        self.addLink(cliente1, switches[0])
        self.addLink(cliente2, switches[0])
        self.addLink(cliente3, switches[-1])
        self.addLink(cliente4, switches[-1])


topos = {'redesTopo': (lambda: RedesTopo())}
