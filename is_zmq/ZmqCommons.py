'''
Created on May 22, 2016

@author: Lakshan Fernando
'''
import os
import sys
import zmq
import time
sys_root = os.path.dirname(os.path.realpath(__file__)).replace('is_zmq', '')
sys.path.append(sys_root)
from ISLogger import Logger


class Zmq_Commons():
    
    def __init__(self):
        pass
    
    
    def zmq_recv(self, sock, timeout = 5000):
        try:
            
            poller = zmq.Poller()
            poller.register(sock, zmq.POLLIN)
            msg = poller.poll(timeout)
            
            if len(msg)>0:
                return sock.recv()
            
            return None
        
        except Exception as ex:
            Logger.log_debug('ERROR @ zmq_recv')
            Logger.log_error(str(ex))
            return None
        finally:
            pass
        
    def connect_zmq(self, ip, port, timeout=5000):
        
        try:
            context = zmq.Context()
            sock = context.socket(zmq.REQ)
            sock.setsockopt(zmq.LINGER, timeout)
            sock.connect('tcp://%s:%s' % (ip, port))
            time.sleep(0.5)
            
            return sock
        except Exception as e:
            Logger.log_debug('ERROR @ Zmq_Commons -> connect_zmq')
            Logger.log_error(str(e))
            return None