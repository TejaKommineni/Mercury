from kafka import KafkaProducer
import configparser
from kafka import TopicPartition
class Producer:
    
    def extractConfigurations(self,fileName):
        config = configparser.ConfigParser()
        config.read(fileName) 
        
    def publish(self):  
        producer = KafkaProducer(bootstrap_servers=['127.0.0.1:9092'],api_version=(0,10))
        i=0
        
        while i<10:
            producer.send('test', b'Hello Kafka' )
            producer.send('test1', b'Bye Kafka' )            
            i=i+1
        producer.close(1)    
        print(producer.partitions_for('test'))
        
    def __init__(self):
        self.producer_properties = {}    

prod = Producer()
prod.extractConfigurations('config.ini')
prod.publish()