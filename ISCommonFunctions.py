__author__ = 'Lakshan Fernando'
__Dev_started_date__ = '15th May 2016'

import threading
import time
import json
import hashlib
from ISLogger import Logger
import subprocess
from subprocess import PIPE
import requests
import requests.packages.urllib3
from requests.packages.urllib3.exceptions import InsecureRequestWarning
import urllib

import configs.Configs as cfg
from is_zmq.ZmqCommons import Zmq_Commons as ZC

class Common_Functions():
    __lock_dict_obj=threading.Lock()
    __lock_serial_no=threading.Lock()
    __lock_sha2=threading.Lock()
    __lock_exec = threading.Lock()
    
    @staticmethod
    def send_to_notifiction_queue(dict_msg):
        try:
            zc = ZC()
            en_sock = zc.connect_zmq(cfg.NOTIFICATION_SERVICE_IP, cfg.NOTIFICATION_SERVICE_PORT)
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
        
        
    @staticmethod
    def send_to_cloud(msg_dict):
        try:
            hub_sno = Common_Functions.get_hub_serial_no()
            msg_dict.update({'hub_sno': hub_sno})
            msg_dict.update({'msg_type' :'NOTIFICATION'})
            
            result = (False, '', False)
            for port in cfg.cloud_opened_ports_list: 
                
                notification_type = msg_dict['notification_type']
                
                if notification_type == 'DELAYED_ACK':
                    result = Common_Functions.send_delayed_ack_to_cloud(msg_dict, port, hub_sno)
                else:
                    result = Common_Functions.send_notification_to_cloud(msg_dict, port, hub_sno)
                
                # there is no error reported
                if result[0] == False and result[2] == False:
                    break
                if result[0] == True and result[2] == False:
                    # There is an error returned from cloud
                    # Should not retry with other urls
                    break
                
            #If there is any error sending
            # save the record to be sent later
            
            return result
        except Exception as e:
            return (False, str(e), False)
    
    @staticmethod
    def send_notification_to_cloud(payload, port, hub_sno):
        try:
            url = 'https://hub:%s@%s:%s/node/send_notification_msg' % (hub_sno, cfg.cloud_dns_name, port)

            requests.packages.urllib3.disable_warnings()
            resp = requests.put(url=url, json=json.dumps(payload), verify=False, timeout=20)
            resp_dict = json.loads(resp.text)

            should_retry = False
            return (resp_dict['error'], resp_dict['error_msg'], should_retry)
            
        except Exception as e:
            #print 'ERROR @ External_IP_Publisher -> __send_notification()'
            #print 'ERROR ' + str(e)
            
            return (True, str(e), True)
        
    @staticmethod
    def send_delayed_ack_to_cloud(payload, port, hub_sno):
        try:
            url = 'https://hub:%s@%s:%s/node/delayed_ack' % (hub_sno, cfg.cloud_dns_name, port)

            requests.packages.urllib3.disable_warnings()
            resp = requests.put(url=url, json=json.dumps(payload), verify=False, timeout=20)
            resp_dict = json.loads(resp.text)

            should_retry = False
            return (resp_dict['error'], resp_dict['error_msg'], should_retry)
            
        except Exception as e:
            #print 'ERROR @ External_IP_Publisher -> __send_notification()'
            #print 'ERROR ' + str(e)
            Logger.log_debug("ERROR @ Jobs_Scheduler -> send_delayed_ack_to_cloud()")
            Logger.log_error(str(e))
            return (True, str(e), True)
                               
    @staticmethod
    def save_dictionary_object(file_name,dict_obj):
    
            Common_Functions.__lock_dict_obj.acquire()
            try:
    
                json.dump(dict_obj,file(file_name,'w'))
                return True
    
            except Exception as e:
                Logger.log_debug("ERROR @ save_dictionary_object")
                Logger.log_error(str(e))
                return False
            finally:
                Common_Functions.__lock_dict_obj.release()
    
    @staticmethod
    def load_dictionary_object(file_name):
    
            Common_Functions.__lock_dict_obj.acquire()
    
            try:
    
                dict_obj=json.load(file(file_name))
                return dict_obj
    
            except Exception as e:
                Logger.log_debug("ERROR @ load_dictionary_object")
                Logger.log_error(str(e))
                return None
            finally:
                Common_Functions.__lock_dict_obj.release()
    
    @staticmethod
    def get_hub_serial_no():
    
        Common_Functions.__lock_serial_no.acquire()
        try:
            cpuserial= ""
    
            f=open('/proc/cpuinfo','r')
            for line in f:
                if line[0:6]=='Serial':
                    cpuserial=line[10:26]
                    break
    
            f.close()
    
            return cpuserial.upper()
    
        except Exception as e:
            return "ERROR000000000"
    
        finally:
            Common_Functions.__lock_serial_no.release()
        
    @staticmethod
    def get_sha256_val(value):
    
        Common_Functions.__lock_sha2.acquire()
        try:
    
            ret_val = hashlib.sha256(value).hexdigest()
            return ret_val
    
        except Exception as e:
            return ""
        finally:
            Common_Functions.__lock_sha2.release()
    
        
    
    @staticmethod
    def is_hub_serial_valid(serial_no):

        hub_sno = Shared_Resources.get_hub_serial_no()

        if hub_sno == serial_no.upper():
            return True
        else:
            return False
        
    @staticmethod
    def execute_os_function(args_list, time_out = 5):

        Common_Functions.__lock_exec.acquire()

        try:

            ellapsed_time_seconds=0
            p=subprocess.Popen(args_list,stdin=PIPE,stdout=PIPE,bufsize=20,shell=False)

            pid=p.pid

            return_code=-1
            ret_text = ""

            #Logger.log_debug("Start Polling")
            while p.poll() == None:
                time.sleep(1)
                ellapsed_time_seconds = ellapsed_time_seconds + 1
                ret_text=p.communicate()
                #Logger.log_debug("Inside poller")
                
                if ellapsed_time_seconds>time_out:

                    #Logger.log_debug("Ellapsed time " + str(ellapsed_time_seconds))
                    p.terminate()
                    os.kill(pid,0)
                    p.kill()
                    break

                return_code=p.returncode

            
            return (return_code, ret_text)


        except Exception as e:
            Logger.log_debug("ERROR @ execute_os_function")
            Logger.log_error(str(e))
            return (-1, '')

        finally:
            Common_Functions.__lock_exec.release()
        
    
    