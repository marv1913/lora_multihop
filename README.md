
[![codecov](https://codecov.io/gh/marv1913/lora_multihop/branch/master/graph/badge.svg?token=Q0JEUCJ9ZS)](https://codecov.io/gh/marv1913/lora_multihop)  
  
[documentation of Python code](https://marv1913.github.io/lora_multihop/index.html)  
  
# LoRa Interface for stream based communication  
  
This application provides an interface to communicate over an ad-hoc LoRa network.  The interface can be accessed using a TCP connection.   So you can use streams to send data over the network. The application also implements a routing protocol to send network packages over the LoRa network.   
<img src="https://raw.githubusercontent.com/marv1913/lora_multihop/master/overview.svg">  
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
## deployment  
## integration tests