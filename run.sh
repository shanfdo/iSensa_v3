sudo nohup python /myData/iSensa_v3/ufw_interface/ufw_rules_updator.py 1>/dev/null 2>&1&
sudo nohup python /myData/iSensa_v3/events_trigger/MessageProcessor.py 1>>mp_log.txt 2>&1&
sudo nohup python /myData/iSensa_v3/rest_api/FlaskApp.py 1>>mp_log.txt 2>&1& 
sudo nohup python /myData/iSensa_v3/notifiers/ExtIPCNotifier.py 1>/dev/null 2>&1&
sudo nohup python /myData/iSensa_v3/notifiers/NotificationSenderMQService.py 1>>mp_log.txt 2>&1&
sudo nohup python /myData/iSensa_v3/scheduler/JSMQService.py 1>/dev/null 2>&1&
sudo nohup python /myData/iSensa_v3/serial_interface/SIMQService.py 1>>mp_log.txt 2>&1&

