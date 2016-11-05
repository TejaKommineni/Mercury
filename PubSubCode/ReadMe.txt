#Instructions for Installing Apache Kafka and running the producer-consumer code.

1) Download the Apache Kafka code from the link below:
https://www.apache.org/dyn/closer.cgi?path=/kafka/0.10.1.0/kafka_2.11-0.10.1.0.tgz and un-tar it.

2) Kafka uses ZooKeeper so you need to first start a ZooKeeper server. In the un-tar folder under bin directory there will be a file named 'zookeeper-server-start.sh'. 
Run this file using the following command:
'zookeeper-server-start.sh config/zookeeper.properties'
The server needs a zookeeper.properties file that has configurations for starting up the server.
In the config/zookeeper.properties file change the value of dataDir variable and point it to any of the local directories.
This ZooKeeper server will start on the port 2181.

3)Once the ZooKeeper server is up we need to start kafka-server. In the un-tar folder under bin directory there will be a file named 'kafka-server-start.sh'.
Run this file using the following command:
'kafka-server-start.sh config/server.properties'
The server needs a server.properties file that stores kafka-server's configurations.
The Kafka server will start on the port 9092.

3)Once the above mentioned steps are done. Run the KafkaConsumer class.
A consumer thread will start and keep listening on the port 9092.

4)Run the KakfaProducer class.
A producer thread will start and will send messages on port 9092.

Note:
In Kafka messages are sent to topics by publisher and subscribers listens to those topics. 
In the code I pushed in today. Publisher is sending messgaes for two topics 'test', 'test1' and consumer is also listening on these two topics.

  
  
