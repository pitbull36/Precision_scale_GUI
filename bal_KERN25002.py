#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time, serial

"""
Class for exceptions
"""
class BalanceException(Exception):
    def __init__(self, message, errors):
        super(BalanceException, self).__init__(message)
        self.errors = errors

"""
Class for force balance
"""

class BAL_KERN25002():

    def __init__(self, com_port='', baudrate=9600, timeout=1, read_bytes=800):
        self.com_port = None
        self.baudrate = baudrate
        self.readtimeout = timeout
        self.read_bytes = read_bytes
        self.ins = None
        self.error_thrown = False

    def connect(self, com_port=''):
        try:
            if com_port != None:
                print ("Opening com port", com_port)
                self.com_port = com_port
                self.ins = serial.Serial(self.com_port, baudrate=self.baudrate,
                                         bytesize=serial.EIGHTBITS, parity = serial.PARITY_NONE,
                                         timeout=2, xonxoff=False,
                                         rtscts=False, dsrdtr=False)
            else:
                print ("No instrument specified, exiting...")
                raise BalanceException("Error cannot not discover balance","Cannot Find Balance")

        except Exception as e:
            print("Unexpected Balance Serial Instrument Exception", e)
            raise BalanceException(e,"Unexpected balance exception thrown")


    def close_instrument(self):
        self.ins.close()


    def read_weight(self, stabilised = True, read_sleeptime = 1):
       # see pg 39 for format
       if stabilised:
           response = self.write('s',18)
       else:
           response = self.write('w',18) # ns = not stable, just so I know it was a not stable measurement

       # convert weight and unit values to float and string
       weight = None
       unit = None

       # only use relevant info
       if(self.error_thrown == False):
           weight = float(response[2:12])
           unit = response[13:16].strip()
           sign = ord(response[1:2])
           
           # xheck for negative sign, for some reasons had issues converting to float
           if (sign == 45):
               weight *= -1
           
       # sleep to reduce successive commands being called too quickly
       time.sleep(read_sleeptime)

       return weight, unit


    def write(self,command,number_readbytes=0):
        # Send command to the balance
        self.ins.write(str(command).encode())
        
        # Set up some initial values
        serial_read = b'0'
        response = None
        
        # Read response from the balance
        if(command != 't'):
            serial_read = self.ins.read(number_readbytes) 
            # check response from balance
            response = serial_read.decode() # convert ascii to str
        
        if (serial_read[0:11] == b''):
            self.error_thrown = True
            print("Error received")
            response = None

        return response


    def zero_scale(self):
        # tare function
        self.write('t', 18)
        print("Zero-ing scale")

        # sleep to make sure there is timme to tare before taking measurements
        time.sleep(3)

