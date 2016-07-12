# iSensa_v3
Codecht Home Automation Client

This software module is for Rasberry Pis, in-order to communicate with Codecht Home Automation Cloud Platform.

Certain features are,

1. Flask RestAPI to listen for any incoming messages from Codecht HA cloud
2. Serial Interface to communicate with attached serial devices to Raspberry pi.
    I.e. Usually the attached serial device is a RF signals broadcaster to external devices. 
    Most probably an arduino device with RF transmitter and receiver. 
3. Router External IP changes publisher
4. UFW interface to monitor changes of cloud IP and update rules
5. Jobs scheduler
6. Main Message processor module to process incomming messages as well as auto triggered sensor or scheduled jobs messages.

    
