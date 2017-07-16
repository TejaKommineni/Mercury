# Project Mercury

This is the repository for the Mercury: geo-aware mobile network message 
delivery project.

Intelligent Transportation Systems require a communication conduit for
the agents in the ecosystem. Communicating telemetry between these endpoints,
along with data from other devices in the environment, allows them to
work together and improve safety.

Mercury is an end-to-end messaging system with lightweight state overhead and
publish/subscribe functionality that is aimed at providing this conduit. 
It is designed to flexibly integrate into the mobile network environment
under which it is deployed.

Mercury is comprised of four essential components: message broker,
publish/subscribe system, message adapter, and endpoints.

Message Broker:
message broker is the brain center of the messaging
system. It processes all incoming messages and sends these to relevant
endpoints (via pubsub). The broker calculates Areas of Interest 
for certain message types (e.g., emergencynotifications). 
Data analysis (aggregated decisions, clientstatistics, etc.) 
occur at the broker. It does not concern itself with
how to get the messages to the target endpoint(s); that job falls to
the message adapter.

Publish/Subscribe System:
Mercury needs a pubsub system that can serve a high number of events
with low latency. Apache Kafka has the best combination of low-latency and
message queueing for recovering lost messages.

Message Adapter:
message adapter is the conduit through which pubsub
messages flow through to endpoints. The adapter coordinates sessions
with client endpoints. It forwards client reports and other content to
and from the pubsub. It also maintains pubsub topic subscriptions for
the endpoints.

Endpoints:
endpoints are the producers and consumers of most content in
the messaging system. Client Endpoints run as applications on
ITS-equipped vehicles.  They report in with telemetry, such as their
current position and speed.  Client endpoints also subscribe to
particular consumer messages identified by specified attributes.

Messages:

Messages are the principle and only communication mechanism in
\name. There are two high-level flavors: control and
content. Control messages include session handling (between broker and
endpoints), broker to message adapter communication, and subscription
management (endpoint to pubsub/broker).  Content messages are those
relevant to applications running on endpoints, such as emergency
alerts.



---

## Team members

**Kirk Webb** and **Teja Kommineni**

---

## Directories:

* paper: Workshop paper content for CS6480 course

* related: Related work storage, e.g. academic papers

* notes: Miscellaneous notes and documents.  Includes whiteboard photos.
