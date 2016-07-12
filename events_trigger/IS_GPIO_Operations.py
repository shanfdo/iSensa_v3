__author__ = 'Lakshan Fernando'

import os
import sys

import RPi.GPIO as GPIO
from ISLogger import Logger as log
#from IS_Commons import Attached_Devices_Params as ADP

sys_root = os.path.dirname(os.path.realpath(__file__)).replace('event_trigger', '')
import configs.Configs as cfg

class GPIO_Operations:

    __attached_devices_params=None

    @staticmethod
    def init_gpio_in_bcm_mode():

        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)

        #GPIO_Operations.__attached_devices_params=attached_devices_params
        log.log_debug("GPIO Mode initialized in BCM mode")

    @staticmethod
    def setup_output_pins(output_pin_list):
        pass

    @staticmethod
    def setup_input_pins(input_pin_list):
        pass


    @staticmethod
    def make_gpio_pin_high(bcm_pin_no):
        try:


            if bcm_pin_no in cfg.available_gpio_pins_list:

                log.log_debug("Setting up pin " + str(bcm_pin_no))
                GPIO.setup(bcm_pin_no,GPIO.OUT)
                GPIO.output(bcm_pin_no,GPIO.HIGH)
                return True

            else:
                return False

        except Exception as e:
            log.log_debug("ERROR @ make_gpio_pin_high")
            log.log_error(str(e))
            return False


    @staticmethod
    def make_gpio_pin_low(bcm_pin_no):
        try:

            bcm_pin_no=int(bcm_pin_no)
            if bcm_pin_no in cfg.available_gpio_pins_list:
                GPIO.setup(bcm_pin_no,GPIO.OUT)
                GPIO.output(bcm_pin_no,GPIO.LOW)
                return True
            else:
                return False

        except Exception as e:
            log.log_debug("ERROR @ make_gpio_pin_low")
            log.log_error(str(e))
            return False


    @staticmethod
    def turn_relay_on(bcm_pin_no):
        try:
            #make the pin value LOW to TURN ON  a relay
            if bcm_pin_no in cfg.available_gpio_pins_list:

                GPIO.setup(bcm_pin_no,GPIO.OUT)
                GPIO.output(bcm_pin_no,GPIO.LOW)
                return True

            else:

                return False

        except Exception as e:
            pass


    @staticmethod
    def turn_relay_off(bcm_pin_no):
        try:
            #make the pin value HIGH to TURN OFF  a relay
            if bcm_pin_no in cfg.available_gpio_pins_list:
                GPIO.setup(bcm_pin_no,GPIO.OUT)
                GPIO.output(bcm_pin_no,GPIO.HIGH)
                return True
            else:
                return False

        except Exception as e:
            pass


    @staticmethod
    def clear_gpio():
        try:
            GPIO.cleanup()
        except Exception as e:
            pass

    def __add_callback_events(self):
        pass


    def __remove_callback_events(self):
        pass


