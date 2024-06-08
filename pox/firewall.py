import os
import json

from pox.core import core
import pox.openflow.libopenflow_01 as of
from pox.lib.revent import *
from pox.lib.util import dpidToStr
from pox.lib.addresses import EthAddr
from collections import namedtuple

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

    def _handle_PacketIn(self, event):
        if event.dpid != int(self.parametros["firewallSwitch"]):
            return

        print(event.dpid)

    def _handle_ConnectionDown(self, event):
        self.dirty = True

    @classmethod
    def settearParametros(cls, pathArchivo):
        with open(pathArchivo, "r") as jsonFile:
            data = json.load(jsonFile)
        return data

def launch(path_archivo):
    core.registerNew(Firewall, path_archivo)
