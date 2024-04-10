import unittest

from mininet.net import Mininet
from mininet.topolib import TreeTopo

class TestMininet(unittest.TestCase):

    def test01(self):
        tree4 = TreeTopo(depth=2,fanout=2)

        net = Mininet(topo=tree4)
        net.start()

        h1, h4  = net.hosts[0], net.hosts[3]
        print(h1.cmd('ping -c1 %s' % h4.IP()))

        net.stop()

if __name__ == '__main__':
    unittest.main()
