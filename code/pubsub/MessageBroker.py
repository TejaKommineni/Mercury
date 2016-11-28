#!/usr/bin/env python

from kafka import KafkaProducer
from kafka import KafkaConsumer
from kafka import TopicPartition
import os, sys
import configparser
import threading
import math
import json

sys.path.append(os.path.abspath("../common"))
import pubsubmessage as psm

CONF_DEFAULTS = {
    'bootstrap_servers': '127.0.0.1:9092',
    'enable_auto_commit': 'False',
}

class MessageBroker:
      
    def extractConfigurations(self,fileName):
        config = configparser.SafeConfigParser(CONF_DEFAULTS)
        config.read(fileName)
        self.consumer_properties['bootstrap_servers']=config['PubSub']['bootstrap_servers']
        self.consumer_properties['enable_auto_commit']=bool(config['PubSub']['enable_auto_commit'])
        self.producer = KafkaProducer(bootstrap_servers=config['PubSub']['bootstrap_servers'],api_version=(0,10))

    def subscribe(self):  
        consumer = KafkaConsumer(bootstrap_servers=self.consumer_properties['bootstrap_servers'])
        topics_list=[]
        topics_list.append(TopicPartition('Emergency', 0))
        topics_list.append(TopicPartition('Collision', 0))
        topics_list.append(TopicPartition('Moving_Objects', 0))
        topics_list.append(TopicPartition('Lane_Change_Assistance', 0))
        topics_list.append(TopicPartition('Obstacle', 0))
        topics_list.append(TopicPartition('Congestion', 0))
        topics_list.append(TopicPartition('Blocked', 0))
        topics_list.append(TopicPartition('Area_Of_Interest', 0))
        topics_list.append(TopicPartition('Client_Report', 0))
        topics_list.append(TopicPartition('Echo', 0))
        
        consumer.assign(topics_list)     
        
        for record in consumer:      
            #print(record)
            if(record.topic =='Echo'):
              self.echo_handler(record.value)
            elif(record.topic =='Emergency'):
              self.emergency_handler(record.value) 
            elif(record.topic =='Collision'):
              self.collision_handler(record.value) 
            elif(record.topic =='Moving_Objects'):
              self.moving_handler(record.value) 
            elif(record.topic =='Lane_Change_Assistance'):
              self.lane_change_handler(record.value) 
            elif(record.topic =='Obstacle'):
              self.obstacle_handler(record.value) 
            elif(record.topic =='Congestion'):
              self.congestion_handler(record.value)   
            elif(record.topic =='Blocked'):
              self.block_handler(record.value)   
            elif(record.topic =='Area_Of_Interest'):
              self.aoi_handler(record.value)
            elif(record.topic =='Client_Report'):
              self.clirep_handler(record.value)
    
    # we are publishing the emergency message immediately after receiving.        
    def emergency_handler(self, message): 
         message=message.decode()
         message=json.loads(message)
         message={
             'type': psm.SAFETY.TYPES.EMERGENCY,
             'x_location': message['x_location'],
             'y_location': message['y_location'],
             'radius': 10,
             'value': 'This is an emergency situation'
         }
         self.publish(psm.SAFETY.BROKER_TOPIC, message) 
    def collision_handler(self, message):
        found=False 
        message=message.decode()
        message=json.loads(message)
        print(message)
        for key,value in self.collision_info.items():
            temp=str(key)
            xy=temp.split(',') 
            x1,y1=float(xy[0]),float(xy[1]) 
            x2,y2=float(message['x_location']),float(message['y_location'])
            distance=math.sqrt(math.pow(x2-x1,2)+math.pow(y2-y1,2)) 
            if distance<=2:
               found=True               
               frequency=self.collision_info.pop(key)               
               x1=round(((frequency*x1)+x2)/(frequency+1),3)
               y1=round(((frequency*y1)+y2)/(frequency+1),3) 
               temp=str(x1)+","+str(y1)                  
               self.collision_info[temp]=frequency+1
               break                                    
            
        if found == False:
           key=str(message['x_location'])+","+str(message['y_location'])
           self.collision_info[key]=1  
               
    def moving_handler(self, message):
        print(message)

    def echo_handler(self, message):
        message = message.decode()
        message = json.loads(message)
        message['type'] = psm.UTILITY.TYPES.ECHO
        self.publish(psm.UTILITY.BROKER_TOPIC, message)
        
    def clirep_handler(self, message):
        # FIXME: Testing!
        return
        message=message.decode()
        message=json.loads(message)
        message={
            'type': psm.UTILITY.TYPES.ECHO,
            'cli_id': message['cli_id'],
            'x_location': message['x_location'],
            'y_location': message['y_location'],
            'radius': 5,
            'value': "Echoing back report from client %s" % message['cli_id']
        }
        self.publish(psm.UTILITY.BROKER_TOPIC, message)
        
    def lane_change_handler(self, message):
        message=message.decode()
        message=json.loads(message)
        message = {
            'type': psm.SAFETY.TYPES.LCHANGE,
            'x_location': message['x_location'],
            'y_location': message['y_location'],
            'radius': 5,
            'value': 'This is a lane change message'} 
        self.publish(psm.SAFETY.BROKER_TOPIC, message)
        
    def obstacle_handler(self, message):
        print(message)
        
    def congestion_handler(self, message):
        found=False 
        message=message.decode()
        message=json.loads(message) 
        print(message)        
        for key,value in self.congestion_info.items():
            temp=str(key)
            xy=temp.split(',') 
            x1,y1=float(xy[0]),float(xy[1]) 
            x2,y2=float(message['x_location']),float(message['y_location'])
            distance=math.sqrt(math.pow(x2-x1,2)+math.pow(y2-y1,2)) 
            if distance<=2:
               found=True               
               frequency=self.congestion_info.pop(key)               
               x1=round(((frequency*x1)+x2)/(frequency+1),3)
               y1=round(((frequency*y1)+y2)/(frequency+1),3) 
               temp=str(x1)+","+str(y1)                  
               self.congestion_info[temp]=frequency+1
               break                                    
            
        if found == False:
           key=str(message['x_location'])+","+str(message['y_location'])
           self.congestion_info[key]=1     
        
        
    def block_handler(self, message):
        print(message) 

    def aoi_handler(self, message):
        message=message.decode()
        message=json.loads(message)
        topics_interested=message['aoi_topics']
        #if 'Congestion' in topics_interested:
             
    # The collision scheduler is called frequently with a less timer
    # than congestion event.
    def collision_scheduler(self):       
        collision_info = self.collision_info  
        self.collision_info={}
        for key,value in collision_info.items():
            if value>10:
               temp=str(key)
               xy=temp.split(',') 
               x1,y1=float(xy[0]),float(xy[1])
               message = {
                   'type': psm.SAFETY.TYPES.COLLISION,
                   'x_location': x1,
                   'y_location': y1,
                   'radius': 2,
                   'value': 'A Collision happened in this area'
               }
               self.publish(psm.SAFETY.BROKER_TOPIC, message)
        threading.Timer(10,self.collision_scheduler).start()

    def congestion_scheduler(self):       
        congestion_info = self.congestion_info  
        self.congestion_info={}
        for key,value in congestion_info.items():
            if value>10:
               temp=str(key)
               xy=temp.split(',') 
               x1,y1=float(xy[0]),float(xy[1])
               message = {
                   'type': psm.SAFETY.TYPES.CONGESTION,
                   'x_location': x1,
                   'y_location': y1,
                   'radius': 2,
                   'value': 'This area is experiencing a lot of congestion'
               }
               self.publish(psm.SAFETY.BROKER_TOPIC, message)
        threading.Timer(10,self.congestion_scheduler).start()
        
    def publish(self, topic, message):
         #print("the message published on topic %s is" % topic)
         #print(message)
         message = json.dumps(message)
         self.producer.send(topic, message.encode())
        
    def __init__(self):
        self.consumer_properties={}
        self.congestion_info={}
        self.collision_info={}
        self.producer = None
        threading.Timer(2,self.congestion_scheduler).start()
        threading.Timer(2,self.collision_scheduler).start()
        
        
        
mb = MessageBroker()
mb.extractConfigurations('config.ini')
mb.subscribe()

    
