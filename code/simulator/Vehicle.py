import os,sys
import socket
import threading

sys.path.append(os.path.abspath("../common"))
import eventhandler

class Vehicle:
    EVTYPE = "VehicleRecvEvent"

    def set_location(self,x,y):
        self.x_location=x
        self.y_location=y
      
    def set_speed(self,speed):   
        self.speed=speed 
        
    def set_last_reported_time(self,time):   
        self.last_reported_time=time

    def get_msg(self):
        msg = None
        self.msglock.acquire()
        if len(self.msglist):
            msg = self.msglist.pop(0)
        self.msglock.release()
        return msg
        
    def send_msg(self,host,port,msg):
        return self.socket.sendto(msg,(host,port))

    def listen(self):
        self.recv_thread = threading.Thread(target=self.udp_recv)
        self.recv_thread.daemon = True
        self.recv_thread.start()
        
    def _add_msg(self, msg):
        self.msglock.acquire()
        self.msglist.append(msg)
        self.msglock.release()
        
    def udp_recv(self):
        while True:
            udpmsg = self.socket.recvfrom(65535)
            self._add_msg(udpmsg)
            ev = eventhandler.MercuryEvent(Vehicle.EVTYPE, self.vehicle_id)
            self.evhandler.fire(ev)

    def __init__(self,vehicle_id,x,y,speed,time):
        self.vehicle_id=vehicle_id
        self.x_location=x
        self.y_location=y
        self.speed=speed
        self.last_reported_time=time
        self.evhandler = eventhandler.EventHandler()
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.msglist = []
        self.msglock = threading.Lock()
        self.recv_thread = None
