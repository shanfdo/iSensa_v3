# iSensa_v3
Codecht Home Automation Client
A python firmware for Raspberry Pi,
to communicate with Codecht Home Automation Cloud Platform.

Required Python Version is 2.7

Pre-requisites

1. Flask
2. ZeroMQ
3. apscheduler


Certain features are,

1. Flask RestAPI to listen for any incoming messages from Codecht HA cloud
2. Serial Interface to communicate with attached serial devices to Raspberry pi.
    I.e. Usually the attached serial device is a RF signals broadcaster to external devices. 
    Most probably an arduino device with RF transmitter and receiver. 
3. Router External IP changes publisher
4. UFW interface to monitor changes of cloud IP and update rules
5. Jobs scheduler
6. Main Message processor module to process incomming messages as well as auto triggered sensor or scheduled jobs messages.

    
