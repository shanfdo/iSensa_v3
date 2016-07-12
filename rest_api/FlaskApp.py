from flask import Flask, jsonify
from flask import make_response
from flask import request
from flask import abort
from flask.ext.httpauth import HTTPBasicAuth
import json
#from flask import View
import sys
import os
import time
from datetime import datetime
from dateutil import parser
import zmq
import ssl
from lib2to3.btm_utils import rec_test
sys_root = os.path.dirname(os.path.realpath(__file__)).replace('rest_api', '')
sys.path.append(sys_root)
import configs.Configs as cfg
from ISLogger import Logger
from ISCommonFunctions import Common_Functions as CF
app = Flask(__name__)
auth = HTTPBasicAuth()

@app.route('/isensa/process_msg', methods = ['POST'])
@auth.login_required
def process_msg():
    
    ack = cfg.ack_dict.copy()
    try:
        
        payload = json.loads(request.json)
        
        if not payload == None:
            
            if not __validate_msg_time(payload['rec_dt']):
                # IP address should be black listed
                #----------------------------------
                ack.update({'comid': payload['comid'], 'comexecstat': 'DONE', 'comcompstat': 'FAILED', 'comresult':'Invalid payload'})
                ack.update({'ack_dt': datetime.utcnow().isoformat(), 'error': True})
                return jsonify(ack)
            
            context = zmq.Context()
            sock = context.socket(zmq.REQ)
            sock.setsockopt(zmq.LINGER, 15000)
            sock.connect('tcp://%s:%s' % (cfg.msg_proc_ip, cfg.msg_proc_port))
            time.sleep(0.5)
            sock.send(json.dumps(payload), zmq.NOBLOCK)

            
            #Wait for the ack
            #----------------
            response = __recv(sock, 15000)
            
            if response == None:
                ack.update({'comid': payload['comid'], 'comexecstat': 'DONE', 'comcompstat': 'FAILED', 'comresult':'No response from MP'})
                ack.update({'ack_dt': datetime.utcnow().isoformat(), 'error': True})
            else:
                response = json.loads(response)
                sock.close()
                del sock
                return jsonify(response)
                
        else:
            ack.update({'comid': payload['comid'], 'comexecstat': 'DONE', 'comcompstat': 'FAILED', 'comresult':'Invalid payload'})
            ack.update({'ack_dt': datetime.utcnow().isoformat(), 'error': True})
            
        
        return jsonify(ack)
    
    except Exception as e:
        Logger.log_debug('ERROR @ FlaskApp -> process_msg')
        Logger.log_error(str(e))

        response_payload = {'error' : True, 'error_msg':'failed at hub gateway'}
        return jsonify(response_payload)


@auth.verify_password
def __authenticate_hub(username, password):
    
    try:
        hashed_hub_sno = CF.get_sha256_val(CF.get_hub_serial_no().upper())
        if password == hashed_hub_sno :
            return True
        else:
            abort(401)
    except Exception as ex:
        abort(401)
    
def __validate_msg_time(rec_dt):
    
    try:
        curr_time = datetime.utcnow()
        rec_dt = parser.parse(rec_dt)
        
        dif = (curr_time - rec_dt).total_seconds()
        
        if dif >= cfg.record_dt_max_valid_seconds:
            Logger.log_warning('Too old payload received : curr time {} and payload time {}'.format(curr_time, rec_dt))
            return False
        else:
            return True
        
    except Exception as e:
        return False
        
def __recv(sock, timeout = 5000):
    try:
        
        poller = zmq.Poller()
        poller.register(sock, zmq.POLLIN)
        msg = poller.poll(timeout)
        
        if len(msg)>0:
            return sock.recv()
        
        return None
    
    except Exception as ex:
        Logger.log_debug('ERROR @ FlaskApp -> __recv()')
        Logger.log_error(str(ex))
        return None
    finally:
        pass
    
@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': True, 'error_msg': 'Not Found'}), 404)

@app.errorhandler(405)
def not_found(error):
    return make_response(jsonify({'error': True, 'error_msg': 'Method not allow.'}), 405)

@app.errorhandler(401)
def auth_error(error):
    return make_response(jsonify({'error': True, 'error_msg': 'Authentication failed.'}), 401)

if __name__ == '__main__':
    context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
    #context = ('/myData/iSensa_v3/certs/servercert','/myData/iSensa_v3/certs/serverkey' )
    context.load_cert_chain('/myData/iSensa_v3/certs/servercert','/myData/iSensa_v3/certs/serverkey')
    app.run(debug=True, host = cfg.hub_internal_ip, port = cfg.hub_opened_port, ssl_context = context, threaded = True, use_reloader=False)
    



