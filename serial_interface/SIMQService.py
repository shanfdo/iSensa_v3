__Start_date__ ='18thJune2016'

import json
import time
import datetime
import os
import sys
#import threading
import glob
import zmq
import multiprocessing
sys_root = os.path.dirname(os.path.realpath(__file__)).replace('serial_interface', '')
#sys_root = sys_root.replace('rest_api','').replace('source', '')
sys.path.append(sys_root)

from ISLogger import Logger
from scheduler.JobScheduler import Jobs_Scheduler as JS
from is_zmq.ZmqCommons import Zmq_Commons as ZC
import configs.Configs as cfg
from SerialInterface import Serial_Interface as SI

class SI_MQ_Service:
    
    def __init__(self):
        self.zc = ZC()
        self.sock = None
        self.q_input = multiprocessing.Queue()
        self.q_i_lock = multiprocessing.Lock()
        if self.__init_zmq_server():
            self.__start_si_mp()
        
    def __init_zmq_server(self):

        try:
            context = zmq.Context()
            self.sock = context.socket(zmq.REP)
            self.sock.setsockopt(zmq.LINGER, 5000)
            self.sock.bind('tcp://%s:%s' % (cfg.SI_MQ_SERVICE_IP, cfg.SI_MQ_SERVICE_PORT))
            
            return True
        except Exception as e:
            Logger.log_debug('ERROR @ SI_MQ_Service -> __init_mq_server')
            Logger.log_error(str(e))
            return False
        finally:
            Logger.log_info('ZMQ server for IS initialized')
            
    def __start_si_mp(self):
        try:
            
            p = SI('si', self.q_input, self.q_i_lock, os.getpid())
            p.start()
            
        except Exception as e:
            Logger.log_debug('ERROR @ SI_MQ_Service -> __start_si_mp()')
            Logger.log_error(str(e))
    
    def run(self):
        try:
            Logger.log_info('ZMQ server for IS started.')
            while True:
                time.sleep(0.5)
                self.__process_mq_msg()
        
        except Exception as e:
            Logger.log_debug('ERROR @ SI_MQ_Service -> run()')
            Logger.log_error(str(e))
            
    def __process_mq_msg(self):
        ret_msg = {'error' : False}
        try:
            msg = self.zc.zmq_recv(self.sock, 5000)
            
            if not msg == None:
                #Write to the sender Q
                msg = json.loads(msg)
                
                self.q_i_lock.acquire()
                try:
                    #Logger.log_debug_1('Adding a message to SIMPQ')
                    self.q_input.put(msg)
                
                except Exception as ex:
                    Logger.log_debug('ERROR @ SI_MQ_Service -> __process_mq_msg() -> sending to Q')
                    Logger.log_error(str(ex))
                    ret_msg.update({'error': True})
                finally:
                    self.q_i_lock.release()
                    self.sock.send(json.dumps(ret_msg))
                    
        except Exception as e:
            Logger.log_debug('ERROR @ SI_MQ_Service -> __process_mq_msg()')
            Logger.log_error(str(e))
        finally:
            pass
        
        
if __name__ == '__main__':

    try:
        sms = SI_MQ_Service()
        sms.run()
    except KeyboardInterrupt:
        quit()
    