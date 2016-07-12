__Start_date__ ='08May2016'

# This is the main application to run for job scheduler
# This does the following
# 1. Initialize job Scheduler
# 2. Listen for incoming ZMQ JS messages

import json
import time
import datetime
import os
import sys
#import threading
import glob
import zmq
sys_root = os.path.dirname(os.path.realpath(__file__)).replace('scheduler', '')
#sys_root = sys_root.replace('rest_api','').replace('source', '')
sys.path.append(sys_root)

from ISLogger import Logger
from scheduler.JobScheduler import Jobs_Scheduler as JS
from is_zmq.ZmqCommons import Zmq_Commons as ZC
import configs.Configs as cfg

class JS_MQ_Service():
    
    def __init__(self):
        
        self.zc = ZC()
        self.sock = None
        self.scheduler = JS()
        self.__init_zmq_server()
    
    def __init_zmq_server(self):

        try:
            context = zmq.Context()
            self.sock = context.socket(zmq.REP)
            self.sock.setsockopt(zmq.LINGER, 5000)
            self.sock.bind('tcp://%s:%s' % (cfg.JS_SERVICE_IP, cfg.JS_SERVICE_PORT))
            
        except Exception as e:
            Logger.log_debug('ERROR @ Job JS_MQ_Service -> __init_mq_server')
            Logger.log_error(str(e))
        finally:
            Logger.log_info('ZMQ server for JS initialized')
        
    #----------------------------------------
    # Read and process all incomming messages
    #----------------------------------------
    def run(self):
        
        self.scheduler.start_scheduler()
        while True:
            try:
                
                time.sleep(0.5)
                self.__process_mq_msg()
            
            except (KeyboardInterrupt, SystemExit):
                quit()
            except Exception as e:
                break
        
    def __process_mq_msg(self):
        try:
            msg = self.zc.zmq_recv(self.sock, 5000)
            if not msg == None:
                payload = json.loads(msg)
                
                #There can be two types of records
                # 1. Schedule a job
                # 2. Remove an already scheduled job
                comtype = payload['comtype']
                
                ret_val = False
                if comtype == 'SAE':
                    #change the comtype to EVE before save
                    payload['comtype'] = 'EVE'
                    cron_job_id = str(payload['cronjobid'])
                    m = payload['cronminute']
                    h = payload['cronhour']
                    dow = payload['crondateofweek']
                    
                    ret_val = self.scheduler.schedule_a_job(cron_job_id, m, h, dow, payload)
                    
                    err_msg = ''
                    if ret_val == False:
                        err_msg = 'scheduling failed'
                        
                    ret_dict  = {'error' : False if ret_val else True, 'error_msg': err_msg}
                    self.sock.send(json.dumps(ret_dict))
                    return 
                
                elif comtype == 'DSR':
                    cron_job_id = str(payload['cronjobid'])
                    ret_val = self.scheduler.remove_a_scheduled_job(cron_job_id)
                        
                    ret_dict  = {'error' : False if ret_val[0] else True, 'error_msg': ret_val[1]}
                    self.sock.send(json.dumps(ret_dict))
                    
                else:
                    ret_dict  = {'error' : True, 'error_msg' : 'unknown command type'}
                    self.sock.send(json.dumps(ret_dict))
                    return 
                 
                
            else:
                return None
        except Exception as e:
            Logger.log_debug('ERROR @ Job JS_MQ_Service -> __process_mq_msg')
            Logger.log_error(str(e))
            #ret_dict  = {'error' : True}
            #self.sock.send(json.dumps(ret_dict))
            return None
    
    def __remove_scheduled_job(self, payload):
        try:
            pass
        
        except Exception as e:
            pass

def main_method():
    try:

        #SP.load_sys_properties()
        #Make sure the parameter values are same as the default values
        #js=Jobs_Scheduler()

        #Jobs_Scheduler.init_scheduler()
        js = JS_MQ_Service()
        js.run()
        
        """
        js.scheduler.schedule_a_job("test1","*/1","19,20,21","1")
        js.scheduler.schedule_a_job("test2","22","2","*")
        js.scheduler.schedule_a_job("test3","29","19","*")
        js.scheduler.start_scheduler()

        while True:
            time.sleep(10)
            break

        js.scheduler.schedule_a_job("test4","6","00","*")

        time.sleep(3)
        js.scheduler.print_jobs()
        
        time.sleep(5)
        
        while True:
            time.sleep(5)
            break
        
        quit()
        """
        
    except Exception as e:
        print(str(e))

if "__main__" ==__name__:

    main_method()
    