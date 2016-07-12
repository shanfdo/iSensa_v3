__date__ = '15th May 2016'
__designed_n_dev_by__ = 'Fernando KLC'
import sys
import os
import socket
from datetime import datetime
import threading
import time
sys_root = os.path.dirname(os.path.realpath(__file__)).replace('ufw_interface', '')
script_path = os.path.dirname(os.path.realpath(__file__))  + "/"
sys.path.append(sys_root)

import configs.Configs as cfg
from ISLogger import Logger
from ISCommonFunctions import Common_Functions as CF

# This will be running as a separate severice.
# Also should listen to incoming zmq messages to ban any ips temporaly
# --------------------------------------------------------------------

class Update_UFW_Rules(threading.Thread):
    
    def __init__(self):
        threading.Thread.__init__(self)
    
    def run(self):
        
        try:
            
            while True:
                self.allow_cloud_ip()
                time.sleep(30)
                
        except Exception as e:
            Logger.log_debug('ERRRO @ Update_UFW_Rules -> run()')
            Logger.log_error(str(e))

    def allow_cloud_ip(self):
        # This function allows the cloud ip from UFW
        # Will remove any old ips of cloud dns
        try:
                
                new_cloud_ip = socket.gethostbyname(cfg.cloud_dns_name)
                old_cloud_ip = CF.load_dictionary_object(script_path + "cloud_ip")
                
                if old_cloud_ip == None:
                    # Create a dictionary and add a new rule
                    #---------------------------------------
                    dict = {'cloud_ip':new_cloud_ip,'port':cfg.hub_opened_port, 'last_updated_date' : datetime.utcnow().isoformat()}
                    self.add_remove_ufw_rule(True, str(cfg.hub_opened_port), new_cloud_ip)
                    
                    CF.save_dictionary_object(script_path + "cloud_ip", dict)
                    
                else:
                    # update rule and update ip file
                    #-------------------------------
                    
                    if not (new_cloud_ip + str(cfg.hub_opened_port)) == (old_cloud_ip['cloud_ip'] + str(old_cloud_ip['port'])) :
                        self.add_remove_ufw_rule(False, str(old_cloud_ip['port']), old_cloud_ip['cloud_ip'])
                        self.add_remove_ufw_rule(True, str(cfg.hub_opened_port), new_cloud_ip)
                        dict = {'cloud_ip':new_cloud_ip, 'port':cfg.hub_opened_port, 'last_updated_date' : datetime.utcnow().isoformat()}
                        CF.save_dictionary_object(script_path + "cloud_ip", dict)
                
        except Exception as e:
            
            Logger.log_debug('ERROR @ Update_UFW_Rules -> update_server_rule')
            Logger.log_error(str(e))
        
    def deny_temporally(self, ip, port, ban_minutes = 10):
        pass
    
    def lift_temporally_ban(self):
        #Traverse through the list of banned ips and lift it if 
        # banned period is ellapsed
        pass
    
    def add_remove_ufw_rule(self, add_rule = True, port = "0", ip_address = ""):
        
        try:
            if int(port) > 0 and len(ip_address)>0:
                
                if add_rule:
                    if self.get_existing_rule_id(ip_address, port) <= 0:
                        #args_list = ['echo', 'y', '|', 'sudo','ufw','allow', 'from', ip_address, 'to', 'any', 'port', port]
                        #return CF.execute_os_function(args_list)
                        result = os.system('echo y | sudo ufw allow from %s to any port %s' % (ip_address, port))
                        
                        return (0,result)
                    else:
                        return (0, '')
                else:
                   
                    id = self.get_existing_rule_id(ip_address, port)
                    print 'id is ' + str(id)
                    if id>0:
                        #args_list = ['echo', 'y','|', 'sudo', 'ufw', 'delete', str(id)]
                        result = os.system('echo y | sudo ufw delete %s' % (id))
                        #return CF.execute_os_function(args_list)
                        return (0, result)
                    else:
                        return(0,'')
            else:
                return (0,'')
            
        except Exception as e:
            Logger.log_debug('ERROR @ add_remove_ufw_rule')
            Logger.log_error(str(e))
            return (0,'')
        
    def get_existing_rule_id(self, ip_address, port):
        
        try:
            args_list = ['sudo', 'ufw', 'status','numbered']
            ret_val = CF.execute_os_function(args_list)
            
            if not ret_val[0] == -1:
                ret_text = ret_val[1][0]
                
                lines_list = ret_text.split('\n')
                
                records = []
                if len(lines_list) > 0:
                    for line in lines_list:
                        rec = line.split()
                        records.append(rec)
                        
                for rec in records:
                    
                    if len(rec)>3:
                        
                        if rec[2] == port and rec[5] == ip_address:
                            return int(rec[1].replace(']',''))
                            
                return 0
            else:
                return 0
        except Exception as e:
            Logger.log_error(str(e))
            return 0
        
if __name__ == '__main__':

    try:
        ufw = Update_UFW_Rules()
        ufw.start()
    except KeyboardInterrupt:
        quit()
        
        
    