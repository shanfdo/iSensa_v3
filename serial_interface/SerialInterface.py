__date__='18th June 2016'

import requests
import json
import requests.packages.urllib3
import multiprocessing
import time
import datetime
import os
import sys
#import glob
import serial
sys_root = os.path.dirname(os.path.realpath(__file__)).replace('notifiers', '')
sys.path.append(sys_root)

from ISLogger import Logger
import configs.Configs as cfg
from ISCommonFunctions import Common_Functions as CF

class Serial_Interface(multiprocessing.Process):
    
    def __init__(self, proc_name, q_input, q_i_lock, parent_proc_id):
        
        self.__dict_incoming_serial_msgs = {}
        self.__dict_coms_waiting_for_ack = {}
        self.parent_proc_id = parent_proc_id
        self.proc_name = proc_name
        self.q_input = q_input
        self.q_i_lock = q_i_lock
        self.serial=None
        self.last_msg_wrote_dt = datetime.datetime.now()
        if self.__connect_serial_interface():
            multiprocessing.Process.__init__(self, name=proc_name)
            
        self.__com_sno = 0 # this is for the command id. Max is 999
    
    def __read_q_msg(self):
        self.q_i_lock.acquire()
        try:
            if not self.q_input.empty():
                return self.q_input.get() 
        
        except Exception as e:
            Logger.log_debug('ERROR @ Serial_Interface -> __read_q_msg()')
            Logger.log_error(str(e))
            return None
        finally:
            self.q_i_lock.release()
            
    def __connect_serial_interface(self):
        try:
            
            if not self.serial == None:
                del self.serial
                self.serial = None
            
            Logger.log_info("Connecting to serial port")
            self.serial = serial.Serial(port=cfg.SERIAL_PORT_NAME, baudrate=9600
                                      , parity=serial.PARITY_NONE
                                      , stopbits=serial.STOPBITS_ONE, timeout=0, bytesize=serial.EIGHTBITS)
            
            
            time.sleep(3) #Wait until arduino resets
            
            return True
        except Exception as e:
            Logger.log_debug("ERROR @ Serial_Interface -> __connect_serial_interface")
            Logger.log_error(str(e))
            return False
        
    def __read_msg_from_serial_port(self):
        
        try:
            if not self.serial.isOpen():
                self.serial.open()
            
            if self.serial.inWaiting() > 0:
                msg = self.serial.readline()
                #self.serial.flush()
                self.serial.close()
                return msg.replace('\r\n', '')
            else:
                
                self.serial.close()
                return ""
            
            
        except Exception as e:
            Logger.log_debug("ERROR @ Serial_Interface -> __read_msg_from_serial_port()")
            Logger.log_error(str(e))
            return ""
    
    def __send_msg_to_serial_port(self, msg):
        try:
            if not self.serial == None:
                if not self.serial.isOpen():
                    #self.__connect_serial_interface()
                    self.serial.open()
                    
                Logger.log_debug_1('Writting to serial {}'.format(msg))
                
                msg = msg + '~'
                self.serial.write(msg)
                self.last_msg_wrote_dt = datetime.datetime.now()
                time.sleep(1)
                self.serial.flush()
                self.serial.close()
                
                return True
            else:
                return False
                
        except Exception as e:
            Logger.log_debug("ERROR @ Serial_Interface -> __send_msg_to_serial_port()")
            Logger.log_error(str(e))
            return False
    
    
    def run(self):
        
        try:
            Logger.log_info('Serial Interface Started - PPID ' + str(self.parent_proc_id) + ' PID ' + str(os.getpid()))
            
            while self.is_parent_alive():
                
                try:
                    msg = None
                    
                    elapsed_seconds = (datetime.datetime.now() - self.last_msg_wrote_dt).total_seconds()
                    if elapsed_seconds >= cfg.SI_WAIT_SECONDS_AFTER_SENDING_A_MSG:
                        msg = self.__read_q_msg()
                        
                    gpio_pin_no = ''
                    dev_code = ''
                    
                    # Send the message to the serial interface
                    # -----------
                    if not msg == None:
                        #Send to the serial port
                        #Logger.log_debug_1('Processing serial message @ SI')
                        
                        gpio_pin_no = str(msg['gpiopinno']).zfill(2)
                        gpio_pin_no = msg['analogordigitalpin'] + gpio_pin_no
                        dev_code = msg['devicecode']
                        
                        self.__com_sno += 1
                        if self.__com_sno >= 999:
                            self.__com_sno = 1
                            
                        com_id = str(self.__com_sno).zfill(3)
                        command_msg = '{}{}{}{}'.format(com_id, msg['devicesno'],gpio_pin_no, msg['comcode'], msg['hubid'])
                        
                        
                        self.__dict_coms_waiting_for_ack.update({self.__com_sno:(command_msg, datetime.datetime.now(), msg['comid'], msg['hubid'],msg['u_or_s'],msg)})
                        result = self.__send_msg_to_serial_port(command_msg)
                        
                        if not result:
                            # Send NACK immediately to the notification Q
                            self.__handle_ack_msg(self.__com_sno, 'DONE', 'FAILED', 'FailedReason~failed to transmit at hub')
                        
                    #=================================
                    #Read any incoming serial message
                    #---------------------------------
                    in_msg = self.__read_msg_from_serial_port()
                    
                    if len(in_msg) > 0:
                        send_to_notification = False
                        
                        #Check whether the message had been send to the notification Q already
                        #-------------
                        if in_msg in self.__dict_incoming_serial_msgs:
                            msg_last_dt = self.__dict_incoming_serial_msgs[in_msg]
                            if (datetime.datetime.now() - msg_last_dt).total_seconds() > cfg.RC_DEVICE_NOTIFICATION_REPEAT_GAP_SECONDS:
                                self.__dict_incoming_serial_msgs[in_msg] = datetime.datetime.now()
                                # Send the message to notification Q
                                send_to_notification = True
                        else:
                            self.__dict_incoming_serial_msgs.update({in_msg:datetime.datetime.now()})
                            send_to_notification = True
                        
                        # STart sending to notification Q
                        #-------------------------------
                        if send_to_notification:
                    
                            if in_msg.startswith("RC:"):
                                
                                self.__handle_RC_msgs(in_msg)
                                        
                            elif in_msg.startswith('ACK:'):
                                
                                in_msg = in_msg.replace('~', '').replace('ACK:','')
                                si_com_sno = int(in_msg[0:3])
                                
                                if si_com_sno in self.__dict_coms_waiting_for_ack:
                                    
                                    comp_status = 'FAILED' if in_msg.endswith('NACK') else 'SUCCESS'
                                    exec_status = 'DONE'
                                    com_results = 'FailedReason~failed to execute' if comp_status == 'FAILED' else ''
                                    
                                    self.__handle_ack_msg(si_com_sno, exec_status, comp_status, com_results)
                                    del self.__dict_coms_waiting_for_ack[si_com_sno]
                                
                            else:
                                #Send the message to the notification q immediately
                                pass
                            
                    # TIMEOUT any command wating for an ACK.
                    #----------------------------------------
                    m_w_s = cfg.SI_MAX_WAIT_SECONDS_FOR_ACK
                    to_del = []
                    
                    for key, val in self.__dict_coms_waiting_for_ack.items():
                        com_dt = val[1]
                        curr_dt = datetime.datetime.now()
                        diff_s = (curr_dt-com_dt).total_seconds()
                        
                        if diff_s > m_w_s:
                            
                            if self.__handle_ack_msg(key, 'DONE', 'FAILED', 'FailedReason~timed out at hub'):
                                to_del.append(key)
                            break #Process only one at a time.
                        
                    for i in to_del:
                        del self.__dict_coms_waiting_for_ack[i]
                        
                                
                    to_del = []
                    
                except Exception as e2:
                    Logger.log_debug('ERROR @ Serial_Interface -> internanl loop -> run()')
                    Logger.log_error(str(e2))
                    
                time.sleep(0.5)
        
        except Exception as e:
            Logger.log_debug('ERROR @ Serial_Interface -> run()')
            Logger.log_error(str(e))
            
    def __handle_RC_msgs(self, msg_line):
        
        try:
                
                # Load the device attributes file
                device_dict = self.__load_rfd_file(msg_line.split(':')[1])
                
                if not device_dict == None:
                    msg_dict = {'notification_type' : 'SERIAL_EVENT', 'notification_dt': datetime.datetime.now().strftime("%Y%m%d %H%M%S")}
                    msg_dict.update({'devicecode': device_dict['devicecode']})
                    msg_dict.update({'hubcondeviceid': device_dict['hubcondeviceid']})
                    msg_dict.update({'cronjobid' : 0})
                    msg_dict.update({'comcode' : 'AUTO_TRIGGER'})
                    msg_dict.update({'comexecstat' : 'DONE'})
                    msg_dict.update({'comcompstat': 'SUCCESS'})
                    msg_dict.update({'comresults' : ''})
                    
                    if device_dict['devicecode'] == 'SRFDOOR':
                        msg_dict.update({'comresult' : 'OPENED'})
                        
                    CF.send_to_notifiction_queue(msg_dict)
        
        except Exception as e:
            Logger.log_debug('ERROR @ Serial_Interface -> __handle_RC_msgs()')
            Logger.log_error(str(e))
            return None
        
    def __handle_ack_msg(self, si_com_sno, exec_status, comp_status, com_result):
        
        try:
            
            server_com_id = self.__dict_coms_waiting_for_ack[si_com_sno][2]
            hub_id = self.__dict_coms_waiting_for_ack[si_com_sno][3]
            u_or_s = self.__dict_coms_waiting_for_ack[si_com_sno][4]
            #msg = self.__dict_coms_waiting_for_ack[si_com_sno][5]
            
            
            if u_or_s == 'U': # User triggered event 
                
                msg_dict = {'notification_type' : 'DELAYED_ACK', 'notification_dt': datetime.datetime.now().isoformat()}
                msg_dict.update({'comid': server_com_id})
                msg_dict.update({'comexecstat' : exec_status})
                msg_dict.update({'comcompstat': comp_status})
                msg_dict.update({'comresult' : com_result})
                msg_dict.update({'hubid' : hub_id})
                CF.send_to_notifiction_queue(msg_dict)
                
            elif u_or_s == 'S':
                
                
                msg = self.__dict_coms_waiting_for_ack[si_com_sno][5].copy()
                msg_dict = {}
                msg_dict.update({'notification_type' : 'CRON_EVENT'})
                msg_dict.update({'notification_dt': datetime.datetime.now().strftime("%Y%m%d %H%M%S")})
                msg_dict.update({'ack_dt': datetime.datetime.now().isoformat()})
                msg_dict.update({'comid': 0})
                msg_dict.update({'comexecstat' : exec_status})
                msg_dict.update({'comcompstat': comp_status})
                msg_dict.update({'comresult' : com_result})
                msg_dict.update({'hubid' : hub_id})
                msg_dict.update({'cronjobid': msg['cronjobid']})
                msg_dict.update({'devicecode': msg['devicecode']})
                msg_dict.update({'hubcondeviceid': msg['hubcondeviceid']})
                msg_dict.update({'comcode': msg['comcode']})
                
                CF.send_to_notifiction_queue(msg_dict)
            
            
            return True
        except Exception as e:
            Logger.log_debug('ERROR @ Serial_Interface -> __handle_ack_msg()')
            Logger.log_error(str(e))
            return False
        
    def __load_rfd_file(self, device_sno):
        
        try:
            file_name = '{}{}.{}'.format(cfg.REGISTERED_DEVICES_RECORDS_PATH,device_sno,'rfd')
            dict_data = CF.load_dictionary_object(file_name)
            
            return dict_data
        except Exception as e:
            return None
    
    def is_parent_alive(self):

        try:
            if self.parent_proc_id > 0:
                os.kill(self.parent_proc_id, 0)
                return True
            else:
                return True
        except Exception as e:
            return False
        
    
            
            
            
            
            