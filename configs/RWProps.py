__author__ = 'Lakshan Fernando'

import os
import sys
sys_root = os.path.dirname(os.path.realpath(__file__)).replace('configs', '')
sys.path.append(sys_root)
from ISLogger import Logger as log

class RW_Properties:

    def __init__(self,property_file_name,delimiter="="):

        self.property_file_name=property_file_name
        self.__dict_props={}
        self.delimiter=delimiter

    def load_properties(self):

        try:

            self.__dict_props={}
            file_obj=open(self.property_file_name,'r')

            for line in file_obj:
                line=line.strip()

                if not line=='':
                    if not line.startswith("#"):
                        lst=line.split(self.delimiter,1)

                        #prop_name=line.split(self.delimiter,1)[0].strip()
                        #prop_val=line.split(self.delimiter)[1].strip()

                        prop_name=lst[0]
                        prop_value=""
                        if len(lst)>1:
                            prop_val=lst[1]


                        self.__dict_props.update({prop_name:prop_val})

            file_obj.close()
            return True

        except Exception as e:
            log.log_debug("ERROR @ load_properties")
            log.log_error(str(e))
            return False

    def get_property_value(self,property_name):

        try:

            return self.__dict_props[property_name]

        except Exception as e:

            log.log_debug("ERROR @ get_property_value")
            log.log_error(str(e))

            return None


    def write_property(self,property_name,property_value):

        try:
            self.load_properties()

            file_obj=open(self.property_file_name,'r')
            lst_contents=file_obj.readlines()

            file_obj.close()

            property_name_index=-1
            line_counter=0

            for line in lst_contents:
                if line.startswith(property_name):
                    property_name_index=line_counter
                    break

                line_counter=line_counter+1

            if property_name_index>0:
                lst_contents[property_name_index]=property_name+self.delimiter+str(property_value) + "\r\n"
            else:
                lst_contents.append(property_name+self.delimiter+str(property_value)+"\r\n")

            file_obj=open(self.property_file_name,'w')

            for line in lst_contents:
                file_obj.write(line)

            file_obj.close()

            self.load_properties()

        except Exception as e:
            log.log_debug("ERROR @ write_property")
            log.log_error(str(e))
            pass