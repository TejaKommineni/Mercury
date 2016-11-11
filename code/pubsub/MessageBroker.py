from kafka import KafkaProducer
from kafka import KafkaConsumer
from kafka import TopicPartition
import configparser
import threading
import math
import json


class MessageBroker:    
      
    def extractConfigurations(self,fileName):
        config = configparser.ConfigParser()
        config.read(fileName)        
        self.consumer_properties['bootstrap_servers']=config['Consumer']['bootstrap_servers']
        self.consumer_properties['enable_auto_commit']=bool(config['Consumer']['enable_auto_commit'])
                
    def subscribe(self):  
        consumer = KafkaConsumer(bootstrap_servers=['127.0.0.1:9092'])
        topics_list=[]
        topics_list.append(TopicPartition('Emergency', 0))
        topics_list.append(TopicPartition('Collision', 0))
        topics_list.append(TopicPartition('Moving_Objects', 0))
        topics_list.append(TopicPartition('Lane_Change_Assistance', 0))
        topics_list.append(TopicPartition('Obstacle', 0))
        topics_list.append(TopicPartition('Congestion', 0))
        topics_list.append(TopicPartition('Blocked', 0))
        topics_list.append(TopicPartition('Area_Of_Interest', 0))
        
        consumer.assign(topics_list)     
        
        for record in consumer:      
            print(record)       
            if(record.topic =='Emergency'):
              self.emergency_handler(record.value) 
            if(record.topic =='Collision'):
              self.collision_handler(record.value) 
            if(record.topic =='Moving_Objects'):
              self.moving_handler(record.value) 
            if(record.topic =='Lane_Change_Assistance'):
              self.lane_change_handler(record.value) 
            if(record.topic =='Obstacle'):
              self.obstacle_handler(record.value) 
            if(record.topic =='Congestion'):
              self.congestion_handler(record.value)   
            if(record.topic =='Blocked'):
              self.block_handler(record.value)   
            if(record.topic =='Area_Of_Interest'):
              self.aoi_handler(record.value)              
    
    # we are publishing the emergency message immediately after receiving.        
    def emergency_handler(self, message): 
         message=message.decode()
         message=json.loads(message)        
         message={'x_location':message['x_location'],'y_location':message['y_location'],'radius':10, 'value':'This is an emergency situation'} 
         self.publish(message) 
    def collision_handler(self, message):
        found=False 
        message=message.decode()
        message=json.loads(message) 
        print(message)        
        for key,value in self.collision_info.items():
            temp=str(key)
            xy=temp.split(',') 
            x1,y1=float(xy[0]),float(xy[1]) 
            x2,y2=message['x_location'],message['y_location']     
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
    def lane_change_handler(self, message):
        message={'x_location':message['x_location'],'y_location':message['y_location'], 'value':'This is a lane change message'} 
        self.publish(message)
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
            x2,y2=message['x_location'],message['y_location']     
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
             
        
        
     
    # The collision scheduler is called frequently with a less timer than congestion event.    
    def collision_scheduler(self):       
        collision_info = self.collision_info  
        self.collision_info={}
        for key,value in collision_info.items():
            if value>10:
               temp=str(key)
               xy=temp.split(',') 
               x1,y1=float(xy[0]),float(xy[1])
               message={'x_location':x1,'y_location':y1,'radius':2, 'value':'A Collision happened in this area'} 
               self.publish(message)  
        threading.Timer(10,self.collision_scheduler).start()    
                           
    
    def congestion_scheduler(self):       
        congestion_info = self.congestion_info  
        self.congestion_info={}
        for key,value in congestion_info.items():
            if value>10:
               temp=str(key)
               xy=temp.split(',') 
               x1,y1=float(xy[0]),float(xy[1])
               message={'x_location':x1,'y_location':y1,'radius':2, 'value':'This area is experiencing a lot of congestion'} 
               self.publish(message)  
        threading.Timer(10,self.congestion_scheduler).start()
        
    def publish(self,message):
         print("the message published is")
         print(message)
         message = json.dumps(message) 
         producer = KafkaProducer(bootstrap_servers=['127.0.0.1:9092'],api_version=(0,10))   
         producer.send('Message_Broker', message.encode())  
         producer.close(1)
        
    def __init__(self):
        self.consumer_properties={}
        self.congestion_info={}
        self.collision_info={}
        threading.Timer(2,self.congestion_scheduler).start()
        threading.Timer(2,self.collision_scheduler).start()
        
        
        
mb = MessageBroker()
mb.extractConfigurations('config.ini')
mb.subscribe()

    