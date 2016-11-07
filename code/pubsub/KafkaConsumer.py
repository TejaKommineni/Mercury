from kafka import KafkaConsumer
import configparser
from kafka import TopicPartition


class Consumer:
    
      
    def extractConfigurations(self,fileName):
        config = configparser.ConfigParser()
        config.read(fileName)        
        self.consumer_properties['bootstrap_servers']=config['Consumer']['bootstrap_servers']
        self.consumer_properties['enable_auto_commit']=bool(config['Consumer']['enable_auto_commit'])
                
    def subscribe(self):  
        consumer = KafkaConsumer(bootstrap_servers=['127.0.0.1:9092'])  
        #consumer.subscribe('test')
        count=0;
        
        consumer.assign([TopicPartition('test', 0),TopicPartition('test1', 0)])
        partition=consumer.assignment()
        print(partition)        
        # records= consumer.poll(0.01) 
      
        consumer.seek(partition.pop(),1929753)
        for record in consumer:                    
            print(record.partition)
            print(record)
        
    def __init__(self):
        self.consumer_properties = {}
        
        
        
cons = Consumer()
cons.extractConfigurations('config.ini')
cons.subscribe()

    