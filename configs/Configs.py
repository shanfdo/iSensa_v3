

cloud_dns_name = 'codecht.ddns.net'
cloud_opened_port = 6061
cloud_opened_ports_list = [6061, 6062, 6063]

hub_internal_ip = '192.168.0.132'
hub_opened_port=4001

msg_proc_ip ='192.168.0.132'
msg_proc_port = 5001

ufw_service_ip = '192.168.0.132'
ufw_service_port = 5002

JS_SERVICE_IP = '192.168.0.132'
JS_SERVICE_PORT = 5003
SCHEDULED_JOBS_FILES_PATH = '/myData/iSensa_v3/scheduler/'

SI_MQ_SERVICE_IP = '192.168.0.132'
SI_MQ_SERVICE_PORT = 5005
SERIAL_PORT_NAME = '/dev/ttyAMA0'
RC_DEVICE_NOTIFICATION_REPEAT_GAP_SECONDS = 15.0
SI_MAX_WAIT_SECONDS_FOR_ACK = 30
SI_WAIT_SECONDS_AFTER_SENDING_A_MSG = 2
#EVENTS_PROCESSOR_IP = '192.168.0.132'
#EVENTS_PROCESSOR_PORT = 5004

NOTIFICATION_SERVICE_IP = '192.168.0.132'
NOTIFICATION_SERVICE_PORT = 5004
SENT_FAILED_NOTIFICATIONS_FILE_PATH = '/myData/iSensa_v3/data_files/'
SEND_RETRY_INTERVAL_SECONDS = 300

REGISTERED_DEVICES_RECORDS_PATH = '/myData/iSensa_v3/data_files/'

ack_dict = {'msg_type': 'ACK', 'comid': 0, 'comexecstat': 'DONE'
            , 'comcompstat': 'SUCCESS', 'comresult':'', 'ack_dt': None, 'error': False}

event_trigger_types = ['CRON_EVENT', 'SENSOR_EVENT', 'IPC_EVENT']
event_trigger_msg_dict = {'event_trigger_type': ''}

record_dt_max_valid_seconds = 60

available_gpio_pins_list=[2,3,4,14,15,17,18,27,22,23,24,10,9,25,11,8,7,5,6,12,13,19,16,26,20,21]


IPC_MONITOR_INTERVAL_SECONDS = 1800
