__author__ = 'lakshanfefnando'
__version__='1.0.0'

import time
import threading
import sys
#####################################################################
# Logger class
#####################################################################
class Logger:

    __lock_logging=threading.RLock()

    @staticmethod
    def log_info(str_msg):

        Logger.__lock_logging.acquire()

        try:
            time_str=time.strftime('%Y%m%d%H%M%S')
            print("[" + time_str + "] INFO :" + str_msg)
            sys.stdout.flush()
        except Exception as e:
            print(str(e))
        finally:
            Logger.__lock_logging.release()

    @staticmethod
    def log_error(str_msg):
        Logger.__lock_logging.acquire()
        try:
            time_str=time.strftime('%Y%m%d%H%M%S')
            print("[" + time_str + "] ERROR :" + str_msg)
            sys.stdout.flush()
        except Exception as e:
            print(str(e))
        finally:
            Logger.__lock_logging.release()

    @staticmethod
    def log_warning(Msg):
        pass

    @staticmethod
    def log_debug(str_msg):
        Logger.__lock_logging.acquire()
        try:
            time_str=time.strftime('%Y%m%d%H%M%S')
            print("[" + time_str + "] DEBUG :" + str_msg)
            sys.stdout.flush()
        except Exception as e:
            print(str(e))
        finally:
            Logger.__lock_logging.release()


    @staticmethod
    def log_debug_1(str_msg):
        Logger.__lock_logging.acquire()
        try:
            Logger.log_debug(str_msg)
        except Exception as e:
            print(str(e))

        finally:
            Logger.__lock_logging.release()

    @staticmethod
    def log_debug_2(str_msg):
        Logger.__lock_logging.acquire()
        try:
            Logger.log_debug(str_msg)
        except Exception as e:
            print(str(e))
        finally:
            Logger.__lock_logging.release()