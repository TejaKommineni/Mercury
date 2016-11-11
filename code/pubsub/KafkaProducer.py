from kafka import KafkaProducer
import configparser
import json
from kafka import TopicPartition
class Producer:
    
    def extractConfigurations(self,fileName):
        config = configparser.ConfigParser()
        config.read(fileName) 
        
    def publish(self,topic):  
        producer = KafkaProducer(bootstrap_servers=['127.0.0.1:9092'],api_version=(0,10))
        
        # we can include timestamp in message to avoid any duplicates or to ignore messages which have got delayed.
        # we can also include an key value pair called priority to let the system know the severity of the event.
        if(topic == 'Emergency'):
            message={'value':'This is an emergency message', 'x_location':1, 'y_location':1,'speed':50}
          
        if(topic == 'Collision'):
            message={'value':'A collision has happened ahead', 'x_location':2, 'y_location':1,'speed':50}
        
        if(topic == 'Moving_Objects'):
            message={'value':'There are objects moving ahead', 'x_location':2, 'y_location':2,'speed':40}
        
        if(topic == 'Lane_Change_Assistance'):
            message={'value':'I am about to change the lane', 'x_location':1, 'y_location':2,'speed':60}
        
        if(topic == 'Obstacle'):
            message={'value':'This road has been closed', 'x_location':1, 'y_location':2,'speed':60}
        
        if(topic == 'Congestion'):
            message={'value':'There is a severe traffic congestion on this route', 'x_location':4, 'y_location':4,'speed':30}
        
        if(topic == 'Congestion_1'):
            message={'value':'There is a severe traffic congestion on this route', 'x_location':5, 'y_location':5,'speed':30}
        
        if(topic == 'Congestion_2'):
            message={'value':'There is a severe traffic congestion on this route', 'x_location':10, 'y_location':10,'speed':30}
       
        if(topic == 'Congestion_3'):
            message={'value':'There is a severe traffic congestion on this route', 'x_location':100, 'y_location':100,'speed':30}
       
        if(topic == 'Congestion_4'):
            message={'value':'There is a severe traffic congestion on this route', 'x_location':10, 'y_location':90,'speed':30}
        
        if(topic == 'Congestion_5'):
            message={'value':'There is a severe traffic congestion on this route', 'x_location':4, 'y_location':5,'speed':30}
        
        
        if(topic == 'Blocked'):
            message={'value':'This road has been blocked for official movements', 'x_location':1, 'y_location':2,'speed':60}
        
        # We can also let the user request for the area of interest and if any particular topic in that area. This can be a list of topics too.    
        if(topic == 'Area_Of_Interest'):
            message={'value':'I am interested to know about the traffic condition in this area', 'x_location':3, 'y_location':3,'speed':10, 'aoi_x_location':2, 'aoi_y_location':2, 'aoi_radius':2, 'aoi_topics':['Congestion','Collision']}
            
        i=0       
        message = json.dumps(message)
        while i<10:
            producer.send(topic.split('_')[0], message.encode())                   
            i=i+1
        producer.close(1)    
        
        
    def __init__(self):
        self.producer_properties = {}    

prod = Producer()
prod.extractConfigurations('config.ini')
prod.publish('Emergency')
prod.publish('Collision')
prod.publish('Moving_Objects')
prod.publish('Lane_Change_Assistance')
prod.publish('Obstacle')
prod.publish('Congestion')
prod.publish('Congestion_1')
prod.publish('Congestion_2')
prod.publish('Congestion_3')
prod.publish('Congestion_4')
prod.publish('Congestion_5')
prod.publish('Blocked')
prod.publish('Area_Of_Interest')