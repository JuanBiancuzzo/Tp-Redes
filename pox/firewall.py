import dataclasses
import os
import json
from enum import Enum
from dataclasses import dataclass

from pox.core import core
import pox.openflow.libopenflow_01 as of
from pox.lib.revent import *
from pox.lib.util import dpidToStr
from pox.lib.addresses import EthAddr, IPAddr
from collections import namedtuple

# Add your imports here ...
log = core.getLogger()


class Protocolo(Enum):
    TCP = 1
    UDP = 2

@dataclass
class Mensaje:
    protocolo: Protocolo
    srcip: str
    srcport: int
    dstip: str
    dstport: int

class Firewall(EventMixin):
    def __init__(self, pathArchivo):
        self.listenTo(core.openflow)
        print("Enabling Firewall Module")

        self.pathArchivo = pathArchivo
        self.parametros = {}
        self.firewallID = -1
        self.dirty = True

    def _handle_ConnectionUp(self, event):
        if self.dirty:
            self.parametros = Firewall.settearParametros(self.pathArchivo)
            self.firewallID = int(self.parametros["firewallSwitch"])
            self.dirty = False

        if event.dpid == self.firewallID:
            msg = of.ofp_flow_mod()
            # msg.priority = 42
            msg.match.nw_dst = IPAddr("10.0.0.2")
            # msg.match.tp_dst = 80
            msg.actions.append(of.ofp_action_output(port=0))
            print(msg)
            event.connection.send(msg)

    def _handle_PacketIn(self, event):
        if event.dpid != self.firewallID:
            return
        return

        direcciones = event.parsed.find('ipv4') 
        if direcciones is None:
            return

        protocoloParsed = event.parsed.find("tcp")
        protocolo = Protocolo.TCP
        if protocoloParsed is None:
            protocoloParsed = event.parsed.find("udp")
            protocolo = Protocolo.UDP

        print(direcciones.dstip)

        if protocoloParsed is None:
            return

        mensaje = Mensaje(
            protocolo,
            str(direcciones.srcip),
            protocoloParsed.srcport,
            str(direcciones.dstip),
            protocoloParsed.dstport,
        )

        if self.bloquearPaquete(mensaje):
            event.halt = True

    def _handle_ConnectionDown(self, event):
        self.dirty = True

    def bloquearPaquete(self, mensaje):
        print(mensaje)
        for regla in self.parametros["reglas"]:
            pass
        return False

    @classmethod
    def settearParametros(cls, pathArchivo):
        with open(pathArchivo, "r") as jsonFile:
            data = json.load(jsonFile)
        return data

def launch(path_archivo):
    core.registerNew(Firewall, path_archivo)
