#!/usr/bin/env python

import sys, glob
sys.path.insert(0, './gen-py')
sys.path.insert(0, glob.glob('../../lib/py/build/lib.*')[0])

from ThriftTest import ThriftTest
from ThriftTest.ttypes import *
from thrift.transport import TTransport
from thrift.transport import TSocket
from thrift.protocol import TBinaryProtocol
import unittest
import time
from optparse import OptionParser


parser = OptionParser()
parser.set_defaults(framed=False, verbose=1, host='localhost', port=9090)
parser.add_option("--port", type="int", dest="port",
    help="connect to server at port")
parser.add_option("--host", type="string", dest="host",
    help="connect to server")
parser.add_option("--framed", action="store_true", dest="framed",
    help="use framed transport")
parser.add_option('-v', '--verbose', action="store_const", 
    dest="verbose", const=2,
    help="verbose output")
parser.add_option('-q', '--quiet', action="store_const", 
    dest="verbose", const=0,
    help="minimal output")

options, args = parser.parse_args()

class AbstractTest(unittest.TestCase):
  def setUp(self):
    socket = TSocket.TSocket(options.host, options.port)

    # Frame or buffer depending upon args
    if options.framed:
      self.transport = TTransport.TFramedTransport(socket)
    else:
      self.transport = TTransport.TBufferedTransport(socket)

    self.transport.open()

    protocol = self.protocol_factory.getProtocol(self.transport)
    self.client = ThriftTest.Client(protocol)

  def tearDown(self):
    # Close!
    self.transport.close()

  def testVoid(self):
    self.client.testVoid()

  def testString(self):
    self.assertEqual(self.client.testString('Python'), 'Python')

  def testByte(self):
    self.assertEqual(self.client.testByte(63), 63)

  def testI32(self):
    self.assertEqual(self.client.testI32(-1), -1)
    self.assertEqual(self.client.testI32(0), 0)

  def testI64(self):
    self.assertEqual(self.client.testI64(-34359738368), -34359738368)

  def testDouble(self):
    self.assertEqual(self.client.testDouble(-5.235098235), -5.235098235)

  def testStruct(self):
    x = Xtruct()
    x.string_thing = "Zero"
    x.byte_thing = 1
    x.i32_thing = -3
    x.i64_thing = -5
    y = self.client.testStruct(x)

    self.assertEqual(y.string_thing, "Zero")
    self.assertEqual(y.byte_thing, 1)
    self.assertEqual(y.i32_thing, -3)
    self.assertEqual(y.i64_thing, -5)

  def testException(self):
    self.client.testException('Safe')
    try:
      self.client.testException('Xception')
      self.fail("should have gotten exception")
    except Xception, x:
      self.assertEqual(x.errorCode, 1001)
      self.assertEqual(x.message, 'Xception')

    try:
      self.client.testException("throw_undeclared")
      self.fail("should have thrown exception")
    except Exception: # type is undefined
      pass

  def testAsync(self):
    start = time.time()
    self.client.testAsync(2)
    end = time.time()
    self.assertTrue(end - start < 0.2,
                    "async sleep took %f sec" % (end - start))

class NormalBinaryTest(AbstractTest):
  protocol_factory = TBinaryProtocol.TBinaryProtocolFactory()

class AcceleratedBinaryTest(AbstractTest):
  protocol_factory = TBinaryProtocol.TBinaryProtocolAcceleratedFactory()

def suite():
  suite = unittest.TestSuite()
  loader = unittest.TestLoader()

  suite.addTest(loader.loadTestsFromTestCase(NormalBinaryTest))
  suite.addTest(loader.loadTestsFromTestCase(AcceleratedBinaryTest))
  return suite

class OwnArgsTestProgram(unittest.TestProgram):
    def parseArgs(self, argv):
        if args:
            self.testNames = args
        else:
            self.testNames = (self.defaultTest,)
        self.createTests()

if __name__ == "__main__":
  OwnArgsTestProgram(defaultTest="suite", testRunner=unittest.TextTestRunner(verbosity=2))
