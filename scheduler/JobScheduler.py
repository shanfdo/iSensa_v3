from __builtin__ import False
__Start_date__ ='27May2016'

# This is the main application to run for job scheduler
# This does the following
# 1. Initialize job Scheduler
# 2. Listen for incoming ZMQ JS messages

import json
import time
import datetime
import os
import sys
import threading
import glob
from apscheduler.schedulers.background import BackgroundScheduler
sys_root = os.path.dirname(os.path.realpath(__file__)).replace('scheduler', '')
#sys_root = sys_root.replace('rest_api','').replace('source', '')
sys.path.append(sys_root)

from is_zmq.ZmqCommons import Zmq_Commons as ZC
from ISLogger import Logger
from ISCommonFunctions import Common_Functions as CF

import configs.Configs as cfg

class Jobs_Scheduler():
    
    __lock_sending_to_msg_q = threading.Lock()
    
    def __init__(self):
        
        self.__scheduler = None
        self.__init_scheduler()
    
    def __init_scheduler(self):
        try:
            
            self.__scheduler = BackgroundScheduler()
            self.__load_scheduled_jobs()
            
        except Exception as e:
            Logger.log_debug('ERROR @ Job_Scheduler -> __init_scheduler')
            Logger.log_error(str(e))
        finally:
            Logger.log_info('Done with initializing job scheduler service')
        
    def start_scheduler(self):
        self.__scheduler.start()
    
    def stop_scheduler(self):
        self.__scheduler.stop()
    
    def __load_scheduled_jobs(self):

        try:
            file_path = cfg.SCHEDULED_JOBS_FILES_PATH

            for file in glob.glob(file_path + "*.shed"):

                dict_msg = CF.load_dictionary_object(file)

                jobid = str(dict_msg["cronjobid"])
                m = str(dict_msg["cronminute"])
                h = dict_msg["cronhour"]
                dow = dict_msg["crondateofweek"]

                self.schedule_a_job(jobid, m, h, dow, None)

        except Exception as e:
            Logger.log_debug("ERROR @ load_scheduled_jobs")
            Logger.log_error(str(e))
    
    def schedule_a_job(self, cronjobid, m="0",h='*',dow='*', message_dict=None):

        #-----------------------------------------
        # jobid format :- <device_com_pk><hub_pk>
        #-----------------------------------------
        ret_val = False
        #Jobs_Scheduler.__job_lock.acquire()
        try:

            if m>=0:

                #dict_obj={"jobid":jobid,"m":m,"h":h,"dow":dow}

                ret_val = True
                if not message_dict == None:
                    
                    file_name = '%s%s%s' % (cfg.SCHEDULED_JOBS_FILES_PATH, cronjobid , ".shed")
                    ret_val = CF.save_dictionary_object(file_name, message_dict)

                if ret_val:
                    #print 'adding a schedule'
                    Logger.log_info('Adding scheduler job ' + str(cronjobid))
                    self.__scheduler.add_job(Jobs_Scheduler.scheduler_callback_function
                                                       ,minute=m,hour=h,day_of_week=dow, id=cronjobid,trigger="cron",kwargs={"jobid":cronjobid})

            return ret_val
        except Exception as e:
            Logger.log_debug("ERROR @ schedule_a_job")
            Logger.log_error(str(e))
            return False
        finally:
            #Jobs_Scheduler.__job_lock.release()
            pass
        
    def remove_a_scheduled_job(self, cronjobid):
        #Jobs_Scheduler.__job_lock.acquire()
        try:

            Logger.log_debug("Removing scheduled job " + cronjobid)
            self.__scheduler.remove_job(cronjobid)
            file_name = cfg.SCHEDULED_JOBS_FILES_PATH + cronjobid + ".shed"
            os.remove(file_name)

            return (True,"")

        except Exception as e:
            Logger.log_debug("ERROR @ remove_a_scheduled_job")
            Logger.log_error(str(e))
            return (False,str(e).replace('u',''))
        finally:
            #Jobs_Scheduler.__job_lock.release()
            pass
        
        
    def print_jobs(self):
        try:
            self.__scheduler.print_jobs()
        
        except Exception as e:
            Logger.log_debug("ERROR @ print_jobs")
            Logger.log_error(str(e))
            
    @staticmethod
    def scheduler_callback_function(jobid):

        Jobs_Scheduler.__lock_sending_to_msg_q.acquire()
        try:
            
            jobid = str(jobid)
            
            Logger.log_info("Scheduler triggered for job "+ jobid)
            file_path = cfg.SCHEDULED_JOBS_FILES_PATH
            file_name = file_path + jobid + ".shed"

            dict_msg = CF.load_dictionary_object(file_name)

            if not dict_msg == None:

                # Send the message to MessageProc q
                result_msg = Jobs_Scheduler.send_job_command(dict_msg)
                
        except Exception as e:
            Logger.log_debug("ERROR @ scheduler_callback_function")
            Logger.log_error(str(e))

        finally:
            Logger.log_debug("End of scheduler_callback_function")
            Jobs_Scheduler.__lock_sending_to_msg_q.release()
            
            
    @staticmethod
    def send_job_command(dict_command):
        try:
            
            cronjobid = dict_command['cronjobid']
            device_code = dict_command['devicecode']
            com_id = dict_command['comid']
            hubcondeviceid = dict_command['hubcondeviceid']
            comcode = dict_command['comcode']
            
            dict_command.update({'u_o_s': 'S'})
            
            zc = ZC()
            mp_sock = zc.connect_zmq(cfg.msg_proc_ip, cfg.msg_proc_port, 15000)
            mp_sock.send(json.dumps(dict_command))
            
            ret_msg = None
            ret_msg = zc.zmq_recv(mp_sock, 15000)
            mp_sock.close()
            del mp_sock

            if not ret_msg == None:
                
                ret_msg = json.loads(ret_msg)
                # Send to notification Q
                
                hub_sno = CF.get_hub_serial_no()
                ret_msg.update({'hub_sno': hub_sno})
                ret_msg.update({'notification_type': 'CRON_EVENT'})
                ret_msg.update({'msg_type' :'NOTIFICATION'})
                ret_msg.update({'notification_dt': datetime.datetime.now().strftime("%Y%m%d %H%M%S")})
                ret_msg.update({'cronjobid': cronjobid})
                ret_msg.update({'devicecode': device_code})
                ret_msg.update({'hubcondeviceid': hubcondeviceid})
                ret_msg.update({'comcode': comcode})
                
                Logger.log_debug('Sending ack to notification queue')
                CF.send_to_notifiction_queue(ret_msg)
            else:
                Logger.log_error('No response back from the message processing queue for the scheduled event.')
            
        except Exception as e:
            Logger.log_debug("ERROR @ Jobs_Scheduler -> send_job_command")
            Logger.log_error(str(e))
    
    """
    @staticmethod
    def send_to_notifiction_queue(dict_msg):
        try:
            zc = ZC()
            en_sock = zc.connect_zmq(cfg.EVENTS_PROCESSOR_IP, cfg.EVENTS_PROCESSOR_PORT)
            en_sock.send(json.dumps(dict_msg))
            
            ret_msg = None
            ret_msg = zc.zmq_recv(en_sock)
            en_sock.close()
            del en_sock
            
            if ret_msg == None:
                return False
            else:
                return True
            
        except Exception as e:
            Logger.log_debug("ERROR @ Jobs_Scheduler -> send_to_notifiction_queue()")
            Logger.log_error(str(e))
            return False
    """
    
    
    