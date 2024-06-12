import os
import json

from pox.core import core
import pox.openflow.libopenflow_01 as of
from pox.lib.revent import *
from pox.lib.util import dpidToStr
from pox.lib.addresses import IPAddr
import pox.lib.packet as pkt

# Add your imports here ...
log = core.getLogger()

class Firewall(EventMixin):
    def __init__(self, pathArchivo):
        self.listenTo(core.openflow)
        print("Enabling Firewall Module")

        self.pathArchivo = pathArchivo
        self.parametros = {}
        self.dirty = True

    def _handle_ConnectionUp(self, event):
        if self.dirty:
            self.parametros = Firewall.settearParametros(self.pathArchivo)
            self.dirty = False

        if event.dpid == int(self.parametros["firewallSwitch"]):
            for regla in self.parametros["reglas"]:
                Firewall.crearRegla(event.connection, regla)

    def _handle_ConnectionDown(self, event):
        self.dirty = True

    @classmethod
    def crearRegla(cls, connection, regla):

        reglaKeys = regla.keys()
        protocolos = [
            pkt.ipv4.UDP_PROTOCOL,
            pkt.ipv4.TCP_PROTOCOL
        ]

        if "protocolo" in reglaKeys:
            if regla["protocolo"] == "UDP":
                protocolos = [ pkt.ipv4.UDP_PROTOCOL ]
            else:
                protocolos = [ pkt.ipv4.TCP_PROTOCOL ]

        for protocolo in protocolos:

            msg = of.ofp_flow_mod()

            msg.match.dl_type = pkt.ethernet.IP_TYPE
            if "ipProtocolo" in reglaKeys and regla["ipProtocolo"] == "ipv6":
                msg.match.dl_type = pkt.ethernet.IPV6_TYPE

            if "puertoDestino" in reglaKeys:
                msg.match.tp_dst = regla["puertoDestino"]
            if "puertoOrigen" in reglaKeys:
                msg.match.tp_src = regla["puertoOrigen"]

            if "ipOrigen" in reglaKeys:
                msg.match.nw_src = IPAddr(regla["ipOrigen"])
            if "ipDestino" in reglaKeys:
                msg.match.nw_dst = IPAddr(regla["ipDestino"])

            msg.match.nw_proto = protocolo
            connection.send(msg)

            print(msg)

    @classmethod
    def settearParametros(cls, pathArchivo):
        with open(pathArchivo, "r") as jsonFile:
            data = json.load(jsonFile)
        return data

def launch(path_archivo):
    core.registerNew(Firewall, path_archivo)
