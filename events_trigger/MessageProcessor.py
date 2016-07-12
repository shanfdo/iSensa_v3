
import zmq
import time
import sys
import threading
import os
import json
import datetime
sys_root = os.path.dirname(os.path.realpath(__file__)).replace('events_trigger', '')

sys.path.append(sys_root)
import configs.Configs as cfg
from ISLogger import Logger
from IS_GPIO_Operations import GPIO_Operations as gpio
from is_zmq.ZmqCommons import Zmq_Commons as ZC
from ISCommonFunctions import Common_Functions as CF

class Message_Processor(threading.Thread):
    
    def __init__(self):
        
        try:
            self.sock = None
            self.zc = ZC()
            gpio.init_gpio_in_bcm_mode()
            self.__init_mq_server()
            threading.Thread.__init__(self)
        
        except Exception as e:
            pass
        
    def __init_mq_server(self):
        try:
            context = zmq.Context()
            self.sock = context.socket(zmq.REP)
            self.sock.setsockopt(zmq.LINGER, 15000)
            self.sock.bind('tcp://%s:%s' % (cfg.msg_proc_ip, cfg.msg_proc_port))
        except Exception as e:
            Logger.log_debug('ERROR @ Message_Processor -> __init_mq_server')
            Logger.log_error(str(e))
    
    def run(self):
        
        while True:
            try:
                
                time.sleep(0.5)
                self.__process_mq_msg()
            
            except (KeyboardInterrupt, SystemExit):
                quit()

    def __process_mq_msg(self):
        
        ack = cfg.ack_dict.copy()
        com_id = 0
        try:
            
            msg = self.zc.zmq_recv(self.sock, 15000)
    
            if not msg == None:
                payload = json.loads(msg)
            else:
                return
            
            if not payload == None:
                
                hub_id = payload['hubid']
                com_id = payload['comid']
                com_type =payload['comtype']
                
                if com_type == 'EVE':
                    device_code = payload['devicecode']
                    
                    if device_code == 'GPIOPIN':
                        
                        self.__handle_gpio_coms(payload)
                    
                    if device_code == 'RFLSWITCH' or device_code == 'RFPLSWITCH':
                        
                        self.__handle_rf_command(payload)
                        
                    else:
                        self.__send_invalid_com_ack(payload)
                        
                elif com_type == 'SAE':
                    
                    Logger.log_debug_1('Processing an SAE message')
                    self.__schedule_an_event(payload)
                    
                elif com_type == 'DSR': # Deletion request of a scheduled event
                    Logger.log_debug_1('Processing an DSR message')
                    self.__schedule_an_event(payload)
                    
                elif com_type == 'SRE' or com_type == 'RRS': # Sensor Registration Event or removal event
                    
                    self.__register_or_remove_rf_sensor(payload)
                    
                else:
                    
                    self.__send_invalid_com_ack(payload)
            
        except Exception as e:
            
            try:
                ack.update({'comid': com_id, 'comexecstat': 'DONE', 'comcompstat': 'FAILED', 'comresult':str(e)})
                ack.update({'ack_dt': datetime.datetime.utcnow().isoformat(), 'error': True})
                jack = json.dumps(ack)
                
                Logger.log_debug('ERROR @ __process_mq_msg')
                Logger.log_error(str(e))
                self.sock.send(jack)
            except Exception as e2:
                Logger.log_error(str(e2))

    
    def __send_invalid_com_ack(self, payload):
        
        try:
            Logger.log_debug_1('Invalid command type')
            
            ack = cfg.ack_dict.copy()
            ack.update({'comid': payload['comid'], 'comexecstat': 'DONE', 'comcompstat': 'FAILED', 'comresult':'Invalid com type'})
            ack.update({'ack_dt': datetime.datetime.utcnow().isoformat(), 'error': True})
            jack = json.dumps(ack)
            self.sock.send(jack)
            
        
        except Exception as e:
             Logger.log_error(str(e))
    
    def __schedule_an_event(self, payload):
        ack = cfg.ack_dict.copy()
        try:
            #Connects to JS service Q
            #zc = ZC()
            js_sock = self.zc.connect_zmq(cfg.JS_SERVICE_IP, cfg.JS_SERVICE_PORT)

            if not js_sock == None:
                # Send the message to JS service Q and wait for the response
                js_sock.send(json.dumps(payload), zmq.NOBLOCK)
                ret_msg = None
                ret_msg = self.zc.zmq_recv(js_sock)
                js_sock.close()
                del js_sock
                
                # Process the response back from JS Service Q
                # and send back the ACK to the message sender
                if not ret_msg == None:
                    
                    ret_msg =json.loads(ret_msg)
                    status = 'SUCCESS' if ret_msg['error'] == False else 'FAILED'
                    ack.update({'comid': payload['comid'], 'comexecstat': 'DONE', 'comcompstat': status, 'comresult': ret_msg['error_msg']})
                    ack.update({'ack_dt': datetime.datetime.utcnow().isoformat(), 'error': ret_msg['error']})
                    
                else:
                    
                    ack.update({'comid': payload['comid'], 'comexecstat': 'DONE', 'comcompstat': 'FAILED', 'comresult':'No response from JS'})
                    ack.update({'ack_dt': datetime.datetime.utcnow().isoformat(), 'error': True})
                
                Logger.log_debug_1('Sending ACK/NACK from MP')
                self.sock.send(json.dumps(ack))
                
            else:
                Logger.log_debug_1('MP failed to connect with JS service')
                ack.update({'comid': payload['comid'], 'comexecstat': 'DONE', 'comcompstat': 'FAILED', 'comresult':'Failed to connect with JS'})
                ack.update({'ack_dt': datetime.datetime.utcnow().isoformat(), 'error': True})
                self.sock.send(json.dumps(ack))
                
        except Exception as e:
            Logger.log_debug('ERROR @ Message_Processor -> __schedule_an_event()')
            Logger.log_error(str(e))
            ack.update({'comid': payload['comid'], 'comexecstat': 'DONE', 'comcompstat': 'FAILED', 'comresult':str(e)})
            ack.update({'ack_dt': datetime.datetime.utcnow().isoformat(), 'error': True})
            self.sock.send(json.dumps(ack))

    def __handle_gpio_coms(self, payload = None):
        
        ack = cfg.ack_dict.copy()
        try:
            com_code = payload['comcode']
            gpio_pin = payload['gpiopinno']
            bcm_pin = payload['bcmgpiopinno']
            
            ret_val = False
            if com_code == 'ON':
                ret_val = gpio.make_gpio_pin_high(bcm_pin)
            else:
                ret_val = gpio.make_gpio_pin_low(bcm_pin)
                
            if ret_val:
                ack.update({'comid': payload['comid'], 'comexecstat': 'DONE', 'comcompstat': 'SUCCESS', 'comresult':''})
                ack.update({'ack_dt': datetime.datetime.utcnow().isoformat()})
            else:
                ack.update({'comid': payload['comid'], 'comexecstat': 'DONE', 'comcompstat': 'FAILED', 'comresult':'Failed gpio operation'})
                ack.update({'ack_dt': datetime.datetime.utcnow().isoformat()})
            
            Logger.log_debug('MP sending ack')
            self.sock.send(json.dumps(ack))
            
        except Exception as e:
            ack.update({'comid': payload['comid'], 'comexecstat': 'DONE', 'comcompstat': 'FAILED', 'comresult':str(e)})
            ack.update({'ack_dt': datetime.datetime.utcnow().isoformat(), 'error': True})
            jack = json.dumps(ack)
            self.sock.send(jack)
            Logger.log_debug('ERROR @ __handle_gpio_coms')
            Logger.log_error(str(e))
            
    def __register_or_remove_rf_sensor(self, payload = None):
        
        ack = cfg.ack_dict.copy()
        
        try:
            com_type = payload['comtype']
            devicesno = payload['devicesno']
            devicecode = payload['devicecode']
            reg_dt = datetime.datetime.now().isoformat()
            hubcondeviceid =payload['hubcondeviceid']
            
            file_path = cfg.REGISTERED_DEVICES_RECORDS_PATH
            file_name = '{}{}.{}'.format(file_path, devicesno, 'rfd')
            
            ret_val = False
            if com_type == 'SRE':
                
                Logger.log_info("Registering a new RF device {}".format(devicesno))
                record_dict = {'devicesno': devicesno, 'devicecode': devicecode, 'reg_dt': reg_dt, 'hubcondeviceid': hubcondeviceid}
                ret_val = CF.save_dictionary_object(file_name , record_dict)
                
            elif com_type == 'RRS':
                # remove registered sensor
                Logger.log_info("Removing a registered sensor {}".format(devicesno))
                os.remove(file_name)
                
                ret_val = True
                
            #Construct ack and send back
            if ret_val:
                
                # Construct an ack
                ack.update({'comid': payload['comid'], 'comexecstat': 'DONE', 'comcompstat': 'SUCCESS', 'comresult':''})
                ack.update({'ack_dt': datetime.datetime.utcnow().isoformat()})
            else:
                ack.update({'comid': payload['comid'], 'comexecstat': 'DONE', 'comcompstat': 'FAILED', 'comresult':'Failed to register'})
                ack.update({'ack_dt': datetime.datetime.utcnow().isoformat()})
            
            self.sock.send(json.dumps(ack))
            
        except Exception as e:
            ack.update({'comid': payload['comid'], 'comexecstat': 'DONE', 'comcompstat': 'FAILED', 'comresult':str(e)})
            ack.update({'ack_dt': datetime.datetime.utcnow().isoformat(), 'error': True})
            jack = json.dumps(ack)
            self.sock.send(jack)
            Logger.log_debug('ERROR @ __register_or_remove_rf_sensor')
            Logger.log_error(str(e))
            
    def __handle_rf_command(self, payload = None):
        ack = cfg.ack_dict.copy()
        try:
            
            #Start sending the message to the Serial Interface Q
            
            zc = ZC()
            si_sock = zc.connect_zmq(cfg.SI_MQ_SERVICE_IP, cfg.SI_MQ_SERVICE_PORT, 5500)
            si_sock.send(json.dumps(payload))
            
            ret_msg = None
            ret_msg = zc.zmq_recv(si_sock, 5500)
            si_sock.close()
            del si_sock
            
            if not ret_msg == None:
                ret_msg = json.loads(ret_msg)
                print ret_msg
                if not ret_msg['error']:
                    ack.update({'comid': payload['comid'], 'comexecstat': 'EXEC', 'comcompstat': 'UNKNOWN', 'comresult':'executing at hub'})
                    ack.update({'ack_dt': datetime.datetime.utcnow().isoformat(), 'error': False})
                    
                else:
                    ack.update({'comid': payload['comid'], 'comexecstat': 'DONE', 'comcompstat': 'FAILED', 'comresult':'failed at serial interface'})
                    ack.update({'ack_dt': datetime.datetime.utcnow().isoformat(), 'error': True})
            else:
                ack.update({'comid': payload['comid'], 'comexecstat': 'DONE', 'comcompstat': 'FAILED', 'comresult':'failed to process'})
                ack.update({'ack_dt': datetime.datetime.utcnow().isoformat(), 'error': True})
                    
            jack = json.dumps(ack)
            self.sock.send(jack)
        
        except Exception as e:
            ack.update({'comid': payload['comid'], 'comexecstat': 'DONE', 'comcompstat': 'FAILED', 'comresult':'failed to handle com'})
            ack.update({'ack_dt': datetime.datetime.utcnow().isoformat(), 'error': True})
            jack = json.dumps(ack)
            self.sock.send(jack)
            Logger.log_debug('ERROR @ Message_Processor -> __handle_rf_command()')
            Logger.log_error(str(e))
    
if __name__ == '__main__':

    try:
        mp = Message_Processor()
        mp.start()
    except KeyboardInterrupt:
        quit()
        
        