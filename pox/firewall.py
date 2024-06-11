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
                break

    def _handle_ConnectionDown(self, event):
        self.dirty = True

    @classmethod
    def crearRegla(cls, connection, regla):
        msg = of.ofp_flow_mod()
        msg.match.dl_type = pkt.ethernet.IP_TYPE
        msg.match.nw_src = IPAddr("10.0.0.1")
        connection.send(msg)

        print(msg)

    @classmethod
    def settearParametros(cls, pathArchivo):
        with open(pathArchivo, "r") as jsonFile:
            data = json.load(jsonFile)
        return data

def launch(path_archivo):
    core.registerNew(Firewall, path_archivo)
