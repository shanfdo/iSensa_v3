__Started_date__ = '02nd June 2016'

import requests
import json
import requests.packages.urllib3
from requests.packages.urllib3.exceptions import InsecureRequestWarning
import urllib
import datetime
import time
import os
import sys
import re
#import threading

sys_root = os.path.dirname(os.path.realpath(__file__)).replace('notifiers', '')
sys.path.append(sys_root)

import configs.Configs as cfg
from ISCommonFunctions import Common_Functions as CF
from ISLogger import Logger as log

class External_IP_Publisher():
    
    def __init__(self):
        #threading.Thread.__init__(self)
        pass
    
    def run(self):
        while True:
            self.__publish_external_ip()
            time.sleep(cfg.IPC_MONITOR_INTERVAL_SECONDS)
    
    
    def __get_external_ip(self):

        try:
            
            log.log_debug('Started checking external ip')
            """
            url = "http://checkip.dyndns.org"
            request = urllib.urlopen(url).read()
            the_ip = re.findall(r"\d{1,3}\.\d{1,3}\.\d{1,3}.\d{1,3}", request)
            """
            
            hub_sno = CF.get_hub_serial_no()
            for port in cfg.cloud_opened_ports_list:
                
                url = 'https://hub:%s@%s:%s/node/what_is_my_ip' % (hub_sno, cfg.cloud_dns_name, port)
                
                try:
                    requests.packages.urllib3.disable_warnings()
                    resp = requests.put(url=url, verify=False, timeout=10)
                    resp_dict = json.loads(resp.text)
                    
                    #print resp_dict
                    if resp_dict['error'] == False:
                        return resp_dict['ip_address']
                    
                except Exception as e2:
                    log.log_error(str(e2))
                
            return ''

        except Exception as e:
            log.log_debug("ERROR @ get_external_ip")
            log.log_error(str(e))
            return ''
        
    def __publish_external_ip(self):
        
        try:
            
            ip_address_saved_file = os.path.dirname(os.path.realpath(__file__)) + '/ext_ip.txt'
            dict_saved_ip = CF.load_dictionary_object(ip_address_saved_file)
            
            old_ip = ""
            external_ip = self.__get_external_ip()
            
            if external_ip == '':
                return 

            has_ip_changed = False
            
            if dict_saved_ip == None:
                has_ip_changed = True
                old_ip = external_ip
                
            else:
                old_ip = dict_saved_ip['external_ip'] 
                if not old_ip == external_ip:
                    has_ip_changed = True
                    
            if has_ip_changed:
                # Start publishing the ip before saving if it has changed
                hub_sno = CF.get_hub_serial_no()
                payload = {'msg_type':'notification', 'notification_type': 'IPC_EVENT', 'new_ip': external_ip
                           , 'old_ip': old_ip, 'hub_sno': hub_sno }
                
                result = (False, '', False)
                for port in cfg.cloud_opened_ports_list:
                    #result = self.__send_notification(payload, port, hub_sno)
                    result = CF.send_notification_to_cloud(payload, port, hub_sno)
                    
                    # there is no error reported
                    if result[0] == False and result[2] == False:
                        break
                    if result[0] == True and result[2] == False:
                        # There is an error returned from cloud
                        # Should not retry with other urls
                        break
                    
                #Save the ip if publishing was successful
                
                if not result[0]:
                    dict_ip = {'external_ip' : external_ip}
                    print 'saving ip addres inside ' + ip_address_saved_file
                    CF.save_dictionary_object(ip_address_saved_file, dict_ip)
                
        except Exception as ex:
            print 'ERROR @ External_IP_Publisher -> __publish_external_ip()'
            print str(ex)
    """
    def __send_notification(self, payload, port, hub_sno):
        
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
    """    
    
def main_method():

    r = External_IP_Publisher()
    r.run()

if "__main__" ==__name__:

    main_method()
