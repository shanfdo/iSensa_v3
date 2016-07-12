from Crypto.SelfTest.Random.test__UserFriendlyRNG import multiprocessing
__Started_date__ = '27th May 2016'

import json
import time
import datetime
import os
import sys
#import threading
import zmq
import multiprocessing
sys_root = os.path.dirname(os.path.realpath(__file__)).replace('notifiers', '')
sys.path.append(sys_root)

from ISLogger import Logger
from ISCommonFunctions import Common_Functions as CF
from is_zmq.ZmqCommons import Zmq_Commons as ZC
import configs.Configs as cfg
from notifiers.NotificationSenderToCloud import Notification_Sender_To_Cloud as NSTC

class Notification_Sender_MQService():
    
    def __init__(self):
        self.list_msgs = []
        self.sock = None
        self.zc = ZC()
        self.q_input = multiprocessing.Queue()
        self.q_i_lock = multiprocessing.Lock()
        
        if self.__init_zmq_server():
            self.__start_sender_mp()
    
    def __init_zmq_server(self):

        try:
            
            Logger.log_info("Initiating Notification Sender MQService")
            context = zmq.Context()
            self.sock = context.socket(zmq.REP)
            self.sock.setsockopt(zmq.LINGER, 2000)
            self.sock.bind('tcp://%s:%s' % (cfg.NOTIFICATION_SERVICE_IP, cfg.NOTIFICATION_SERVICE_PORT))
            
            return True
        except Exception as e:
            Logger.log_debug('ERROR @ Job Notification_Sender_MQService -> __init_zmq_server')
            Logger.log_error(str(e))
            return False
            
    def __start_sender_mp(self):
        try:
            
            p = NSTC('ntsc', self.q_input, self.q_i_lock, os.getpid())
            p.start()
            
        except Exception as e:
            Logger.log_debug('ERROR @ Notification_Sender_MQService -> __start_sender_mp()')
            Logger.log_error(str(e))
    
    def run(self):
        try:
            Logger.log_info('Notification Sender MQ Service started.')
            while True:
                time.sleep(0.5)
                self.__process_mq_msg()
        
        except Exception as e:
            Logger.log_debug('ERROR @ Notification_Sender_MQService -> run()')
            Logger.log_error(str(e))
    
    def __process_mq_msg(self):
        try:
            msg = self.zc.zmq_recv(self.sock, 5000)
            
            if not msg == None:
                #Write to the sender Q
                msg = json.loads(msg)
                
                self.q_i_lock.acquire()
                try:
                    Logger.log_debug_1('Adding a message to MPQ to be sent to cloud')
                    self.q_input.put(msg)
                
                except Exception as ex:
                    Logger.log_debug('ERROR @ Job Scheduler -> __process_mq_msg() -> sending to Q')
                    Logger.log_error(str(ex))
                finally:
                    self.q_i_lock.release()
                    self.sock.send(json.dumps({'error': False}))
                    
        except Exception as e:
            Logger.log_debug('ERROR @ Job Notification_Sender_MQService -> __process_mq_msg()')
            Logger.log_error(str(e))
        finally:
            pass
        
        
if __name__ == '__main__':

    try:
        ner = Notification_Sender_MQService()
        ner.run()
    except KeyboardInterrupt:
        quit()
        
        