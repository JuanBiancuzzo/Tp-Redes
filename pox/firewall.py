import os

from pox.core import core
import pox.openflow.libopenflow_01 as of
from pox.lib.revent import *
from pox.lib.util import dpidToStr
from pox.lib.addresses import EthAddr
from collections import namedtuple

# Add your imports here ...
log = core.getLogger()

# Add your global variables here ...
class Firewall(EventMixin):
    def __init__(self):
        self.listenTo(core.openflow)
        log.debug("Enabling Firewall Module")
        print("Enabling Firewall Module")

    def _handle_ConnectionUp(self, event):
        print(event)
        print("Hola")

    def _handle_ConnectionDown(self, event):
        print(event)
        print("chau")

    def launch():
        print("launch")

core.registerNew(Firewall)

