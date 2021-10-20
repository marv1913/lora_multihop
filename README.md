
[![codecov](https://codecov.io/gh/marv1913/lora_multihop/branch/master/graph/badge.svg?token=Q0JEUCJ9ZS)](https://codecov.io/gh/marv1913/lora_multihop)  
  

  
# Ad-hoc LoRa network for stream-based communication  
  
This application provides an interface to communicate over an ad-hoc LoRa network.  The interface can be accessed using a TCP connection.  So you can use streams to send data over the network.  All application supporting TCP communication can use the LoRa network for data exchange. The application also implements a routing protocol to send network packages over the LoRa network.  The [documentation of the whole application](https://marv1913.github.io/lora_multihop/index.html)  is hosted in the Github pages of this repository.
<img src="https://raw.githubusercontent.com/marv1913/lora_multihop/master/diagrams/overview.svg">  
## protocol  
The protocol is an ad-hoc multi-hop protocol, which is based on AODV. So you are able to build a network for communicating over long distances.  Detailed specifications of the protocol can be found in under the [wiki page](https://github.com/marv1913/lora_multihop/wiki) of this repository.  
  
## TCP interface  
The application provides two different TCP sockets for communication and interaction:  
  
###  TCP socket for administration  
  
This Socket can be used to control the routing protocol. There are different types of messages, which are sent as Strings to the TCP socket. The fields of these messages are delimited by a `,` and each message is delimited by a `|`.

#### register a peer 
`Registration,peerId,True|`

#### unregister a peer 
`Registration,peerId,False|`

#### get all registered peers 
`registeredPeers?|`

The response on this message looks like:
`peerA,peerB,...|`

#### connect request
`ConnectRequest,sourcePeerId,targetPeerId,timeout|`

#### disconnect request
`DisconnectRequest,sourcePeerId,targetPeerId|`

When a node receives a connect/disconnect request the message will be forwarded to your application using the TCP socket for administration. The format of the forwarded request is identical to the format for sending these request.

### TCP socket for data exchange  
After a successful connect request it is possible to exchange data over the LoRa network using the second TCP socket. All data which are sent to the socket will be forwarded to the LoRa node which was the target peer of the connect request. Data which are received by the LoRa node are sent from the LoRa protocol application to the application, which is connected to the protocol application using the TCP socket for data exchange. So for the applications using the LoRa network for communication it makes no difference whether they are using the LoRa network or a direct TCP connection.
## hardware  
As LoRa modem the Himalaya HIMO-01M is used for this project. The modem is connected to a Raspberry Pi using an UART interface. To control the modem AT-commands are sent to the modem using this UART interface. So each node is made up of a Raspberry Pi and a LoRa modem.
## deployment  
For following steps are necessary to deploy the application:
- install requirements listed in [requirements  file](https://github.com/marv1913/lora_multihop/blob/master/requirements.txt): `pip3 install -r requirements.txt`
- run main-method defined in [main.py](https://github.com/marv1913/lora_multihop/blob/master/src/main.py): `python3 main.py`
  - before calling the main-method it is possible to adjust in the `main.py` file parameters like the modem-configuration, modem address or the ports for the TCP sockets
## integration tests
The tests are written in Java. There are two stages defined in the file [HubIPCJavaSideIntegrationTest.java](https://github.com/marv1913/lora_multihop/blob/master/integration_test/java/lora_integration_test/HubIPCJavaSideIntegrationTest.java).  Because the Tests have dependencies from [ASAPHub](https://github.com/SharedKnowledge/ASAPHub) the tests are also available as an executable jar: [integration_tests.jar](https://github.com/marv1913/lora_multihop/blob/master/integration_test/integration_tests.jar). To make it possible to run the integration tests without providing a real LoRa network the application was extended by the modules `local_network.py` and `local_network_multihop.py` These modules can be used to build a virtual LoRa network locally. So each instance of this module represents one LoRa node. The instances of this module are connected using TCP.  The virtual LoRa network can be built using two different ways:
### using docker containers
The virtual LoRa network can be built on linux systems where docker is installed  using the script `start_integration_test_container.sh`:
- to build virtual network containing two nodes you have to run the following command from the root path of this repository: 
`./integration_test/two_nodes/start_integration_test_container.sh`
- to build virtual network containing threed nodes (to test multi-hop) you have to run the following command from the root path of this repository: 
`./integration_test/multihop/start_integration_test_container.sh`

### start nodes manually
The nodes of the virtual LoRa network also can be setup manually.
- to build a virtual network containing two nodes you have to start two instances of the python module [integration_test.py](https://github.com/marv1913/lora_multihop/blob/master/src/integration_test.py)
-  to build virtual network containing threed nodes (to test multi-hop) you have to start three instances of the python module [integration_test_multihop.py](https://github.com/marv1913/lora_multihop/blob/master/src/integration_test.py)

The correct variable values for the nodes can be found in the `.env`:
- two nodes: 
  - [node-1](https://github.com/marv1913/lora_multihop/blob/master/integration_test/two_nodes/env_node_1)
  - [node-2](https://github.com/marv1913/lora_multihop/blob/master/integration_test/two_nodes/env_node_2)
- multi-hop:
  - [node-1](https://github.com/marv1913/lora_multihop/blob/master/integration_test/multihop/env_node_1)
  - [node-2](https://github.com/marv1913/lora_multihop/blob/master/integration_test/multihop/env_node_2)
  - [node-3](https://github.com/marv1913/lora_multihop/blob/master/integration_test/multihop/env_node_3)

### build new integration test jar
To build a new jar for the integration tests the following steps are necessary:
- clone the Repository of the  [ASAPHub](https://github.com/SharedKnowledge/ASAPHub)  application
-  copy Java package [lora_integration_test](https://github.com/marv1913/lora_multihop/tree/master/integration_test/java/lora_integration_test) from this repository to the path `tests/net/sharksystem/lora_integration_test` of the ASAPHub repository
- build a new jar defining the class `tests/net/sharksystem/lora_integration_test/TestRunner` as main class