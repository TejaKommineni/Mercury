#!/usr/bin/env python

from Vehicle import Vehicle
import threading
import math
import time
import sys
import os
import socket
import uuid

sys.path.append(os.path.abspath("../common"))
import udpiface 
import mercury_pb2
import eventhandler as evh
import pubsubmessage as psm
import sessionmessage as sm

class Mercury_Simulator:  
 
 # This method is used to send vehicular reports periodically.
 def report_scheduler(self): 
     for id,vehicle in self.vehicles.items():
         last_report_time = self.vehicles[id].last_reported_time
         speed=self.vehicles[id].speed
         present_time=time.time()
         difference=present_time-last_report_time
         if(difference >8):
            if speed == 0:
               self.vehicles[id].x_location=(self.vehicles[id].x_location+1)%self.x_max
               self.vehicles[id].y_location=(self.vehicles[id].y_location)%self.y_max     
            if speed == 1:
               self.vehicles[id].x_location=(self.vehicles[id].x_location+1)%self.x_max
               self.vehicles[id].y_location=(self.vehicles[id].y_location+1)%self.y_max   
            if speed == 2:
               self.vehicles[id].x_location=(self.vehicles[id].x_location+2)%self.x_max
               self.vehicles[id].y_location=(self.vehicles[id].y_location+1)%self.y_max 
            if speed == 3:
               self.vehicles[id].x_location=(self.vehicles[id].x_location+2)%self.x_max
               self.vehicles[id].y_location=(self.vehicles[id].y_location+2)%self.y_max
            self.send_report(id,self.vehicles[id].x_location,self.vehicles[id].y_location,self.vehicles[id].speed)            
            self.vehicles[id].last_reported_time=time.time()  
     threading.Timer(5,self.report_scheduler).start()                                   
 
    
 # This method displays two options to the user either to add vehicles to the system or simulate events in the system.
 def show_options(self):   
    while True: 
        print('Hi! This is Mercury Simulator')
        print('I can perform the following two actions')
        print('1: Add Vehicles To The System')
        print('2: Simulate An Event')
        option=int(input('Please Choose any option:'))
        if option == 1:
           print('Total number of vehicles in the system are :', len(self.vehicles))
           count_vehicles=input('Input the number of vehicles you would like to add to this system')
           self.add_vehicles(int(count_vehicles))
        elif option == 2:
           self.generate_events()
        else:
           print('Your input didnt match the given options. Kindly, select one of the given options')

 # In the show_options when user chooses to add vehicles this method is called.          
 def add_vehicles(self,count_vehicles):
    num_vehicles=len(self.vehicles)
    start=int(math.sqrt(num_vehicles)+1)  
    end=int(math.sqrt(count_vehicles)+1)+start
    x_last=start
    y_last=1
    max_y=1    
    while(x_last<=end and count_vehicles>0):
       while(y_last<=end and count_vehicles>0):
         vehicle=Vehicle(num_vehicles+count_vehicles,x_last,y_last,((num_vehicles+count_vehicles)%4),time.time())
         self.vehicles[num_vehicles+count_vehicles]=vehicle
         vehicle.listen()
         count_vehicles-=1
         y_last+=1
       x_last+=1
       y_last=1
    self.x_max=end
    self.y_max=end 
  
 # The clients added to the system will receive messages through this method on the port they bound. 
 def udp_recv_simulator(self):
     evhandler = evh.EventHandler()
     while True:
         evhandler.wait()
         while evhandler.hasevents():         
             ev = evhandler.pop()
             vehicle_id = int(ev.evdata)
             vehicle = self.vehicles[vehicle_id]
             udpmsg = vehicle.get_msg()
             pmsg = mercury_pb2.MercuryMessage()
             pmsg.ParseFromString(udpmsg[0])
             print "Simulator received a UDP msg for vehicle %d:\n%s" % \
                   (vehicle_id, str(pmsg))

 # Report Scheduler calls this method on a vehicle when it has to send a report. 
 def send_report(self,id,x,y,speed):
     msg=self.generate_report(id,x,y,speed)
     vehicle = self.vehicles[id]
     vehicle.send_msg(self.adapter_addr, self.adapter_port, msg.SerializeToString())

 # This method generates the report digest that has to be send across.
 def generate_report(self,id,x,y,speed):
     outmsg = mercury_pb2.MercuryMessage()
     outmsg.uuid = str(uuid.uuid4())
     outmsg.type = mercury_pb2.MercuryMessage.APP_CLI 
     outmsg.src_addr.type = mercury_pb2.MercuryMessage.CLIENT
     outmsg.src_addr.cli_id = id
     outmsg.dst_addr.type = mercury_pb2.MercuryMessage.ADAPTER
     outmsg.session_msg.type = mercury_pb2.SessionMsg.CLIREP
     outmsg.session_msg.id = 0
     sm.add_msg_attr(outmsg, sm.CLIREP.X_LOC, x)
     sm.add_msg_attr(outmsg, sm.CLIREP.Y_LOC, y)
     sm.add_msg_attr(outmsg, sm.CLIREP.DIRECTION, 0)
     sm.add_msg_attr(outmsg, sm.CLIREP.SPEED, speed)
     return outmsg
          
 # This method is invoked when the user selects to simulate an event in show_options method             
 def generate_events(self):
     print('Which of the following event type would you like to simulate')
     print('1: Emergency')
     print('2: Collision')
     print('3: Moving_Objects')
     print('4: Lane_Change_Assistance')
     print('5: Obstacle')
     print('6: Congestion')
     print('7: Blocked')
     option=int(input('Please Choose any option:'))
     if option == 1:
        x,y,r = self.event_location() 
        self.simulate_events(1,x,y,r) 
     if option == 2:
        x,y,r = self.event_location() 
        self.simulate_events(2,x,y,r) 
     if option == 3:
        x,y,r = self.event_location() 
        self.simulate_events(3,x,y,r) 
     if option == 4:
        x,y,r = self.event_location() 
        self.simulate_events(4,x,y,r) 
     if option == 5:
        x,y,r = self.event_location() 
        self.simulate_events(5,x,y,r) 
     if option == 6:
        x,y,r = self.event_location() 
        self.simulate_events(6,x,y,r) 
     if option == 7:
        x,y,r = self.event_location() 
        self.simulate_events(7,x,y,r)    
                 
 # This method helps in calculating the location of event at which you would like to simulate the event       
 def event_location(self):
     print('Would you like to look at the vehicle distribution before issuing the event')
     print('1:Yes')
     print('2:No')
     choice=int(input('Please Choose any option:'))
     if choice == 1:
           boundary=self.x_max
           reminder=boundary%5
           start=(boundary-reminder)/5           
           clusters={}
           clusters[start]=0
           clusters[start*2]=0
           clusters[start*3]=0
           clusters[start*4]=0
           clusters[boundary]=0
           for id,vehicle in self.vehicles.items():
               for center,count in clusters.items():
                   if self.vehicles[id].x_location<=center and self.vehicles[id].y_location<=center:
                       clusters[center]=count+1
           
           print("The vehicles in the system are grouped into 5 clusters.")
           print('{:15}'.format('Cluster_Center'), '{:15}'.format('Cluster_Radius'), '{:15}'.format('Vehicle_Count'))
           for center,count in clusters.items():
               print('{:13}'.format('('+ str(center/2)+','+str(center/2)+')'), '{:13}'.format(center/2), '{:13}'.format(count))
           while True:
               print('You can custom query me to know the number of vehicles in a given region') 
               print('1:Yes')
               print('2:No')
               choice=int(input('Please Choose any option:'))
               if choice == 1:
                   x=int(input('Enter the x coordinates of the querying region'))
                   y=int(input('Enter the y coordinates of the querying region'))
                   radius=int(input('Enter the querying radius with center being above x,y coordinates'))
                   count=0
                   for id,vehicle in self.vehicles.items():
                        x_v=self.vehicles[id].x_location
                        y_v=self.vehicles[id].y_location
                        if(math.sqrt(math.pow((x_v-x), 2)+math.pow((y_v-y), 2))<=radius):
                          count+=1  
                   print('The count of vehicles in the queried region is', count)       
                   
               
               if choice == 2:  
                   x=int(input('Enter the x coordinates where you want to issue the event'))
                   y=int(input('Enter the y coordinates where you want to issue the event'))
                   radius=int(input('Enter the impact radius with center being above x,y coordinates'))
                   return x,y,radius 
              
           
            
     if choice == 2:
       x=int(input('Enter the x coordinates where you want to issue the event'))
       y=int(input('Enter the y coordinates where you want to issue the event'))
       radius=int(input('Enter the impact radius with center being above x,y coordinates'))
       return x,y,radius 
 
 # The generate_events method after determining the event location calls the simulate events method
 def simulate_events(self,type,x,y,r):         
        count=0 
        for id,vehicle in self.vehicles.items():
            x_v=self.vehicles[id].x_location
            y_v=self.vehicles[id].y_location
            if(math.sqrt(math.pow((x_v-x), 2)+math.pow((y_v-y), 2))<=r):
               count+=1 
               self.send_event(type,id,x_v,y_v)
               print("I have seen a collision and my id is", id, x_v, y_v)   
               
        print("Total number of vehicles impacted is", count)   
 
 # For each vehicle that falls under the area of simulation send_event method is called             
 def send_event(self, type,id, x, y):
     if type == 1:         
        event='I am an Emergency Event'  
        msg=self.generate_msg('Emergency',event,id,x,y)
     elif type == 2:         
        event='I am a Collision Event'  
        msg=self.generate_msg('Collision',event,id,x,y) 
     elif type == 3:         
        event='I see a Moving Object Infront'  
        msg=self.generate_msg('Moving_Objects',event,id,x,y)   
     elif type == 4:         
        event='I am changing the lane'  
        msg=self.generate_msg('Lane_Change_Assistance',event,id,x,y)   
     elif type == 5:         
        event='I see a Obstacle Infront'  
        msg=self.generate_msg('Obstacle',event,id,x,y)   
     elif type == 6:         
        event='There is a lot of Congestion in this location'  
        msg=self.generate_msg('Congestion',event,id,x,y)   
     elif type == 7:         
        event='The road is blocked for any vehicular movement'  
        msg=self.generate_msg('Blocked',event,id,x,y)   

     vehicle = self.vehicles[id]
     return vehicle.send_msg(self.adapter_addr,self.adapter_port,msg.SerializeToString())
 
 # The generate_msg helps send_event method by returning a message digest that has to be sent when event occurred.
 def generate_msg(self,topic,msg,id,x,y):
     outmsg = mercury_pb2.MercuryMessage()
     outmsg.uuid = str(uuid.uuid4())
     outmsg.type = mercury_pb2.MercuryMessage.CLI_PUB
     outmsg.src_addr.type = mercury_pb2.MercuryMessage.CLIENT
     outmsg.src_addr.cli_id = id
     outmsg.dst_addr.type = mercury_pb2.MercuryMessage.PUBSUB
     outmsg.pubsub_msg.topic = topic
     psm.add_msg_attr(outmsg, psm.SAFETY.ATTRIBUTES.X_LOC, x)
     psm.add_msg_attr(outmsg, psm.SAFETY.ATTRIBUTES.Y_LOC, y)
     return outmsg
      

 def __init__(self):
     self.vehicles={}
     self.x_max=1
     self.y_max=1
     self.adapter_addr='127.0.0.1'
     self.adapter_port=8888
     threading.Timer(5,self.report_scheduler).start()
     self.recv_thread = threading.Thread(target=self.udp_recv_simulator)
     self.recv_thread.daemon = True
     self.recv_thread.start()
     self.show_options()
        
        
simulator = Mercury_Simulator()             
