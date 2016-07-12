__date__='07th June 2016'

import requests
import json
import requests.packages.urllib3
import multiprocessing
import time
import datetime
import os
import sys
import glob
import dateutil.parser

sys_root = os.path.dirname(os.path.realpath(__file__)).replace('notifiers', '')
sys.path.append(sys_root)

from ISLogger import Logger
import configs.Configs as cfg
from ISCommonFunctions import Common_Functions as CF

class Notification_Sender_To_Cloud(multiprocessing.Process):
    
    def __init__(self, proc_name, q_input, q_i_lock, parent_proc_id):
        
        self.parent_proc_id = parent_proc_id
        self.proc_name = proc_name
        self.q_input = q_input
        self.q_i_lock = q_i_lock
        multiprocessing.Process.__init__(self, name=proc_name)
        #self.name = proc_name
    
    def run(self):
        
        try:
            Logger.log_info('Started PPID ' + str(self.parent_proc_id) + ' PID ' + str(os.getpid()))
            while self.is_parent_alive():
                msg = self.__read_q_msg()
                if not msg == None:
                    #Send to the cloud
                    Logger.log_debug_1('Sending a message to cloud')
                    
                    result = CF.send_to_cloud(msg)
                    
                    if result[0]:
                        self.__save_sent_failed_notification(msg)
                else:
                    self.__re_try_failed_notifications()
                    #pass
                time.sleep(0.5)
        
        except Exception as e:
            Logger.log_debug('ERROR @ Notification_Sender_To_Cloud -> run()')
            Logger.log_error(str(e))
    
    def is_parent_alive(self):

        try:
            if self.parent_proc_id > 0:
                os.kill(self.parent_proc_id, 0)
                return True
            else:
                return True
        except Exception as e:
            return False
    
    def __read_q_msg(self):
        self.q_i_lock.acquire()
        try:
            if not self.q_input.empty():
                return self.q_input.get() 
        
        except Exception as e:
            Logger.log_debug('ERROR @ Notification_Sender_To_Cloud -> __read_q_msg()')
            Logger.log_error(str(e))
            return None
        finally:
            self.q_i_lock.release()
    
    
    def __save_sent_failed_notification(self, msg_dict):
        try:
            
            msg_dict.update({'last_sent_failed_dt': datetime.datetime.now().isoformat()})
            path = cfg.SENT_FAILED_NOTIFICATIONS_FILE_PATH
            file_name = '{}{}.{}'.format(path, datetime.datetime.now().strftime('%Y%m%d%H%M%S%f'), 'sfn')
            CF.save_dictionary_object(file_name, msg_dict)
        except Exception as e:
            Logger.log_debug('ERROR @ Notification_Sender_To_Cloud -> __save_sent_failed_notification()')
            Logger.log_error(str(e))
    

    def __re_try_failed_notifications(self):
        
        try:
            
            path = cfg.SENT_FAILED_NOTIFICATIONS_FILE_PATH
            
            for file in glob.glob(path + "*.sfn"):
                dict_msg = CF.load_dictionary_object(file)
                
                last_sent_failed_dt  = dateutil.parser.parse(dict_msg['last_sent_failed_dt'])
                curr_dt = datetime.datetime.now()
                
                if (curr_dt - last_sent_failed_dt).total_seconds() < cfg.SEND_RETRY_INTERVAL_SECONDS:
                    continue
                
                result = CF.send_to_cloud(dict_msg)
                    
                if result[0] == False:
                    # Delete the file
                    os.remove(file)
                    break
                    # Break is added to limit just one message at a time to be sent to cloud
                elif result[0] and result[2] == False:
                    os.remove(file)
                    break
                else:
                    # Retry after XX minutes
                    # Update the message and re-save
                    dict_msg.update({'last_sent_failed_dt': datetime.datetime.now().isoformat()})
                    os.remove(file)
                    CF.save_dictionary_object(file, dict_msg)
                    break
                
        except Exception as e:
            Logger.log_debug('ERROR @ Notification_Sender_To_Cloud -> __re_try_failed_notifications()')
            Logger.log_error(str(e))
        
        
        