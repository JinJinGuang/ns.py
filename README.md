# ns.py: A Pythonic Discrete-Event Network Simulator

This discrete-event network simulator is based on [`simpy`](https://simpy.readthedocs.io/en/latest/), which is a general-purpose discrete event simulation framework for Python. `ns.py` is designed to be flexible and reusable, and can be used to connect multiple networking components together easily, including packet generators, network links, switch elements, schedulers, traffic shapers, traffic monitors, and demultiplexing elements.

# Installation

First, launch the terminal and create a new `conda` environment (say, called `ns.py`):

```shell
$ conda update conda
$ conda create -n ns.py python=3.8
$ conda activate ns.py
```

Then, install `ns.py` using `pip`:

```shell
$ pip install ns.py
```

That's it! You can now try to run some examples in the `examples/` directory. More examples will be added as existing components are refined and new components are introduced.

## Computer Networking

### Delay

See [delay](https://zh.wikipedia.org/wiki/%E6%97%B6%E5%BB%B6).

<img src="img/1625987838790.png" alt="1625987838790" style="zoom:50%;" />

- [Processing delay](https://en.wikipedia.org/wiki/Processing_delay) – time it takes a router to process the packet header
- [Queuing delay](https://en.wikipedia.org/wiki/Queuing_delay) – time the packet spends in routing queues
- [Transmission delay](https://en.wikipedia.org/wiki/Transmission_delay) – time it takes to push the packet's bits onto the link
- [Propagation delay](https://en.wikipedia.org/wiki/Propagation_delay) – time for a signal to propagate through the media

## Current Network Components

The network components that have already been implemented include:

### Packet (Customer or Job)

* `Packet`: a simple representation of a network packet, carrying its creation time, size, packet id, flow id, source and destination.

  ```python
  class Packet:
      """
      Packets in ns.py are generally created by packet generators, and will run through a queue at an output port.
      Parameters
      ----------
      time: float (creation time)
          the time when the packet is generated.
      size: float
          the size of the packet in bytes, which (in bytes) field is used to determine its transmission time.
      packet_id: int
          an identifier for the packet
      src, dst: int
          identifiers for the source and destination
      flow_id: int or str
          an integer or string that can be used to identify a flow (customer type?)
      """
      def __init__(self,
                   time,
                   size,
                   packet_id,
                   src="source",
                   dst="destination",
                   flow_id=0):
  ```

### Packet Generator (Source)

* `DistPacketGenerator`: generates packets according to provided distributions of inter-arrival times and packet sizes.

  ```python
  class DistPacketGenerator:
      """ 
      Generates packets with a given inter-arrival time distribution.
      Parameters
      ----------
      env: simpy.Environment
          The simulation environment.
      element_id: str
          the ID of this element (generator).
      arrival_dist: function
          A no-parameter function that returns the successive inter-arrival times of
          the packets.
      size_dist: function
          A no-parameter function that returns the successive sizes of the packets.
      initial_delay: number
          Starts generation after an initial delay. Defaults to 0.
      finish: number
          Stops generation at the finish time. Defaults to infinite.
      rec_flow: bool
          Are we recording the statistics of packets generated? (size and creation time)
      """
      def __init__(self,
                   env,
                   element_id,
                   arrival_dist,
                   size_dist,
                   initial_delay=0,
                   finish=float("inf"),
                   flow_id=0,
                   rec_flow=False,
                   debug=False):
  ```

* `TracePacketGenerator`: generates packets according to a trace file, with each row in the trace file representing a packet.

* `TCPPacketGenerator`: generates packets using TCP as the transport protocol.

### Sink (Destination)

* `PacketSink`: receives packets and records delay statistics.

  ```python
  class PacketSink:
      """ 
  	A PacketSink is designed to record both arrival times and waiting times from the incoming packets.
      Parameters
      ----------
      env: simpy.Environment
          the simulation environment
      rec_arrivals: bool
          if True, arrivals will be recorded
      absolute_arrivals: bool
          if True absolute arrival times will be recorded, otherwise the time between
          consecutive arrivals (inter-arrival time) is recorded.
      rec_waits: bool
          if True, the waiting times experienced by the packets are recorded
      rec_flow_ids: bool
          if True, the flow IDs that the packets are used as the index for recording;
          otherwise, the 'src' field in the packets are used
      debug: bool
          If True, prints more verbose debug information.
      """
      def __init__(self,
                   env,
                   rec_arrivals: bool = True,
                   absolute_arrivals: bool = True,
                   rec_waits: bool = True,
                   rec_flow_ids: bool = True,
                   debug: bool = False):
  ```

* `TCPSink`: receives packets, records delay statistics, and produces acknowledgements back to a TCP sender.

### Port

* `Port`: an output port on a switch with a given rate and buffer size (in either bytes or the number of packets), using the simple tail-drop mechanism to drop packets.

  ```python
  class Port:
      """ 
      Model an output port on a switch with a given rate and buffer size (in either bytes or the number of packets), using the simple tail-drop mechanism to drop packets.
      Parameters
      ----------
      env: simpy.Environment
          the simulation environment
      rate: float 
          the bit rate of the port (bps, bit/s)
      element_id: int
          the element id of this port
      qlimit: integer (or None)
          a queue limit in bytes or packets (including the packet in service), beyond
          which all packets will be dropped. Default is the infinie queue limit.
      limit_bytes: bool
          if True, the queue limit will be based on bytes; if False, the queue limit
          will be based on packets.
      zero_downstream_buffer: bool (???)
          if True, assume that the downstream element does not have any buffers,
          and backpressure is in effect so that all waiting packets queue up in this
          element's buffer.
      debug: bool
          If True, prints more verbose debug information.
      """
      def __init__(self,
                   env,
                   rate: float,
                   element_id: int = None,
                   qlimit: int = None,
                   limit_bytes: bool = False,
                   zero_downstream_buffer: bool = False,
                   debug: bool = False):
  ```

* `REDPort`: an output port on a switch with a given rate and buffer size (in either bytes or the number of packets), using the Early Random Detection (RED) mechanism to drop packets.

### Wire

* `Wire`: a network wire (cable) with its propagation delay following a given distribution. There is no need to model the bandwidth of the wire, as that can be modeled by its upstream `Port` or scheduling server.

  ```python
  class Wire:
      """ 
      Implements a network wire (cable) that introduces a propagation delay.
      Set the "out" member variable to the entity to receive the packet.
      Parameters
      ----------
      env: simpy.Environment
          the simulation environment
      delay: float
          a no-parameter function that returns the successive propagation
          delays on this wire
      """
      def __init__(self, env, delay_dist, wire_id=0, debug=False):
  ```

### Splitter

* `Splitter`: a splitter that simply sends the original packet out of port 1 and sends a copy of the packet out of port 2.
* `NWaySplitter`: an n-way splitter that sends copies of the packet to *n* downstream elements.

### Communication Network Component

* `TrTCM`: a two rate three color marker that marks packets as green, yellow, or red (refer to RFC 2698 for more details).
* `RandomDemux`: a demultiplexing element that chooses the output port at random.
* `FlowDemux`: a demultiplexing element that splits packet streams by flow ID.
* `FIBDemux`: a demultiplexing element that uses a Flow Information Base (FIB) to make packet forwarding decisions based on flow IDs.
* `TokenBucketShaper`: a token bucket shaper.
* `TwoRateTokenBucketShaper`: a two-rate three-color token bucket shaper with both committed and peak rates/burst sizes.

### Server

* `SPServer`: a Static Priority (SP) scheduler.
  ![img](https://pic3.zhimg.com/80/v2-cc1707b42ddc9c8bd716f173850bb292_1440w.jpg)

  ```python
  class SPServer:
      """
      Parameters
      ----------
      env: simpy.Environment
          The simulation environment.
      rate: float
          The bit rate of the port.
      priorities: list or dict
          This can be either a list or a dictionary. If it is a list, it uses the flow_id as its index to look for the flow's corresponding priority. If it is a dictionary, it contains (flow_id -> priority) pairs for each possible flow_id.
      zero_buffer: bool
          Does this server have a zero-length buffer? This is useful when multiple
          basic elements need to be put together to construct a more complex element
          with a unified buffer.
      zero_downstream_buffer: bool
          Does this server's downstream element has a zero-length buffer? If so, packets
          may queue up in this element's own buffer rather than be forwarded to the
          next-hop element.
      debug: bool
          If True, prints more verbose debug information.
      """
      def __init__(self,
                   env,
                   rate,
                   priorities,
                   zero_buffer=False,
                   zero_downstream_buffer=False,
                   debug=False) -> None:
  ```

* `WFQServer`: a Weighted Fair Queueing (WFQ) scheduler.
  ![img](https://pic1.zhimg.com/80/v2-6f48339ec6dd887d776bbb7729e9bf94_1440w.jpg)(Idealized model)

  ```python
  class WFQServer:
      """
      Parameters
      ----------
      env: simpy.Environment
          The simulation environment.
      rate: float
          The bit rate of the port.
      weights: list or dict
          This can be either a list or a dictionary. If it is a list, it uses the flow_id as its index to look for the flow's corresponding weight. If it is a dictionary, it contains (flow_id -> weight) pairs for each possible flow_id.
      zero_buffer: bool
          Does this server have a zero-length buffer? This is useful when multiple
          basic elements need to be put together to construct a more complex element
          with a unified buffer.
      zero_downstream_buffer: bool
          Does this server's downstream element has a zero-length buffer? If so, packets
          may queue up in this element's own buffer rather than be forwarded to the
          next-hop element.
      debug: bool
          If True, prints more verbose debug information.
      """
      def __init__(self,
                   env,
                   rate,
                   weights,
                   zero_buffer=False,
                   zero_downstream_buffer=False,
                   debug=False) -> None:
  ```

* `DRRServer`: a Deficit Round Robin (DRR) scheduler.
  ![preview](https://pic1.zhimg.com/v2-7bc3b14dba6c55f2e4ba5ed274524688_r.jpg)

  ```python
  class DRRServer:
      """
      Parameters
      ----------
      env: simpy.Environment
          The simulation environment.
      rate: float
          The bit rate of the port.
      weights: list or dict
          This can be either a list or a dictionary. If it is a list, it uses the flow_id as its index to look for the flow's corresponding weight. If it is a dictionary, it contains (flow_id -> weight) pairs for each possible flow_id.
      zero_buffer: bool
          Does this server have a zero-length buffer? This is useful when multiple basic elements need to be put together to construct a more complex element with a unified buffer.
      zero_downstream_buffer: bool
          Does this server's downstream element have a zero-length buffer? If so, packets may queue up in this element's own buffer rather than be forwarded to the next-hop element.
      debug: bool
          If True, prints more verbose debug information.
      """
      MIN_QUANTUM = 1500
  
      def __init__(self,
                   env,
                   rate,
                   weights: list,
                   zero_buffer=False,
                   zero_downstream_buffer=False,
                   debug=False,
                   out_queue_id=None) -> None:
  ```

* `VirtualClockServer`: a Virtual Clock scheduler.

### Monitor

* `PortMonitor`: records the number of packets in a `Port`. The monitoring interval follows a given distribution.
* `ServerMonitor`: records performance statistics in a scheduling server, such as `WFQServer`, `VirtualClockServer`, `SPServer`, or `DRRServer`.

## Current utilities

* `TaggedStore`: a sorted `simpy.Store` based on tags, useful in the implementation of WFQ and Virtual Clock.

* `Config`: a global singleton instance that reads parameter settings from a configuration file. Use `Config()` to access the instance globally.

## Current Examples (in increasing levels of complexity)

* `basic.py`: A basic example that connects two packet generators to a network wire with a propagation delay distribution, and then to a packet sink. It showcases `DistPacketGenerator`, `PacketSink`, and `Wire`.

* `overloaded_switch.py`: an example that contains a packet generator connected to a downstream switch port, which is then connected to a packet sink. It showcases `DistPacketGenerator`, `PacketSink`, and `Port`.

* `mm1.py`: this example shows how to simulate a port with exponential packet inter-arrival times and exponentially distributed packet sizes. It showcases `DistPacketGenerator`, `PacketSink`, `Port`, and `PortMonitor`.

* `tcp.py`: this example shows how a two-hop simple network from a sender to a receiver, via a simple packet forwarding switch, can be configured, and how acknowledgment packets can be sent from the receiver back to the sender via the same switch. The sender uses a TCP as its transport protocol, and the congestion control algorithm is configurable (such as TCP Reno or TCP CUBIC). It showcases `TCPPacketGenerator`, `CongestionControl`, `TCPSink`, `Wire`, and `SimplePacketSwitch`.

* `token_bucket.py`: this example creates a traffic shaper whose bucket size is the same as the packet size, and whose bucket rate is one half the input packet rate. It showcases `DistPacketGenerator`, `PacketSink`, and `TokenBucketShaper`.

* `two_rate_token_bucket.py`: this example creates a two-rate three-color traffic shaper. It showcases `DistPacketGenerator`, `PacketSink`, and `TwoRateTokenBucketShaper`.

* `wfq.py`: this example shows how to use the Weighted Fair Queueing (WFQ) scheduler, and how to use a server monitor to record performance statistics with a finer granularity using a sampling distribution. It showcases `DistPacketGenerator`, `PacketSink`, `Splitter`, `WFQServer`, and `ServerMonitor`.

* `virtual_clock.py`: this example shows how to use the Virtual Clock scheduler, and how to use a server monitor to record performance statistics with a finer granularity using a sampling distribution. It showcases `DistPacketGenerator`, `PacketSink`, `Splitter`, `VirtualClockQServer`, and `ServerMonitor`.

* `drr.py`: this example shows how to use the Deficit Round Robin (DRR) scheduler. It showcases `DistPacketGenerator`, `PacketSink`, `Splitter` and `DRRServer`.

* `two_level_drr.py`, `two_level_wfq.py`, `two_level_sp.py`: these examples have shown how to construct a two-level topology consisting of Deficit Round Robin (DRR), Weighted Fair Queueing (WFQ) and Static Priority (SP) servers. They also show how to use strings for flow IDs and to use dictionaries to provide per-flow weights to the DRR, WFQ, or SP servers, so that group IDs and per-group flow IDs can be easily used to construct globally unique flow IDs.

* `red_wfq.py`: this example shows how to combine a Random Early Detection (RED) buffer (or a tail-drop buffer) and a WFQ server. The RED or tail-drop buffer serves as an upstream input buffer, configured to recognize that its downstream element has a zero-buffer configuration. The WFQ server is initialized with zero buffering as the downstream element after the RED or tail-drop buffer. Packets will be dropped when the downstream WFQ server is the bottleneck. It showcases `DistPacketGenerator`, `PacketSink`, `Port`, `REDPort`, `WFQServer`, and `Splitter`, as well as how `zero_buffer` and `zero_downstream_buffer` can be used to construct more complex network elements using elementary elements.

* `fattree_fifo.py`: an example that shows how to construct and use a FatTree topology for network flow simulation. It showcases `DistPacketGenerator`, `PacketSink`, and `SimplePacketSwitch`.

## Writing New Network Components

To design and implement new network components in this framework, you will first need to read the [10-minute SimPy tutorial](https://simpy.readthedocs.io/en/latest/simpy_intro/index.html). It literally takes 10 minutes to read, but if that is still a bit too long, you can safely skip the section on *Process Interaction*, as this feature will rarely be used in this network simulation framework.

In the *Basic Concepts* section of this tutorial, pay attention to three simple calls: `env.process()`, `env.run()`, and `yield env.timeout()`. These are heavily used in this network simulation framework.

### Setting up a process

The first is used in our component's constructor to add this component's `run()` method to the `SimPy` environment. For example, in `scheduler/drr.py`:

```python
self.action = env.process(self.run())
```

Keep in mind that not all network components need to be run as a *SimPy* process (more discussions on processes later). While traffic shapers, packet generators, ports (buffers), port monitors, and packet schedulers definitely should be implemented as processes, a flow demultiplexer, a packet sink, a traffic marker, or a traffic splitter do not need to be modeled as processes. They just represent additional processing on packets inside a network.

### Running a process

The second call, `env.run()`, is used by our examples to run the environment after connecting all the network components together. For example, in `examples/drr.py`:

```python
env.run(until=100)
```

This call simply runs the environment for 100 seconds.

### Scheduling an event

The third call, `yield env.timeout()`, schedules an event to be fired sometime in the future. *SimPy* uses an ancient feature in Python that's not well known, *generator functions*, to implement what it called *processes*. The term *process* is a bit confusing, as it has nothing to do with processes in operating systems. In *SimPy*, each process is simply a sequence of timed events, and multiple processes occur concurrently in real-time. For example, a scheduler is a process in a network, and so is a traffic shaper. The traffic shaper runs concurrently with the scheduler, and both of these components run concurrently with other traffic shapers and schedulers in other switches throughout the network.

In order to implement these processes in a network simulation, we almost always use the `yield env.timeout()` call. Here, `yield` uses the feature of generator functions to return an iterator, rather than a value. This is just a fancier way of saying that it *yields* the *process* in *SimPy*, allowing other processes to run for a short while, and it will be resumed at a later time specified by the timeout value. For example, for a Deficit Round Robin (DRR) scheduler to send a packet (in `scheduler/drr.py`), it simply calls:

```python
yield self.env.timeout(packet.size * 8.0 / self.rate)
```

which implies that the scheduler *process* will resume its execution after the transmission time of the packet elapses. A side note: in our network components implemented so far, we assume that the `rate` (or *bandwidth*) of a link is measured in bits per second, while everything else is measured in bytes. As a result, we will need a little bit of a unit conversion here.

What a coincidence: the `yield` keyword in Python in generator functions is the same as the `yield()` system call in an operating system kernel! This makes the code much more readable: whenever a process in *SimPy* needs to wait for a shared resource or a timeout, simply call `yield`, just like calling a system call in an operating system.

**Watch out** for a potential pitfall: Make sure that you call `yield` at least once in *every* path of program execution. This is more important in an infinite loop in `run()`, which is very typical in our network components since the environment can be run for a finite amount of simulation time. For example, at the end of each iteration of the infinite loop in `scheduler/drr.py`, we call `yield`:

```python
yield self.packets_available.get()
```

This works just like a `sleep()` call on a binary semaphore in operating systems, and will make sure that other processes have a chance to run when there are no packets in the scheduler. This is, on the other hand, not a problem in our Weighted Fair Queueing (WFQ) scheduler (`scheduler/wfq.py`), since we call `yield self.store.get()` to retrieve the next packet for processing, and `self.store` is implemented as a sorted queue (`TaggedStore`). This process will not be resumed after `yield` if there are no packets in the scheduler.

### Sharing resources

The *Shared Resources* section of the 10-minute SimPy tutorial discussed a mechanism to request and release (either automatically or manually) a shared resource by using the `request()` and `release()` calls. In this network simulation framework, we will simplify this by directly calling:

```python
packet = yield store.get()
```

Here, `store` is an instance of `simpy.Store`, which is a simple first-in-first-out buffer containing shared resources in *SimPy*. We initialize one such buffer for each flow in `scheduler/drr.py`:

```python
if not flow_id in self.stores:
    self.stores[flow_id] = simpy.Store(self.env)
```

### Sending packets out

How do we send a packet to a downstream component in the network? All we need to do is to call the component's `put()` function. For example, in `scheduler/drr.py`, we run:

```python
self.out.put(packet)
```

after a timeout expires. Here, `self.out` is initialized to `None`, and it is up to the `main()` program to set up. In `examples/drr.py`, we set the downstream component of our DRR scheduler to a packet sink:

```python
drr_server.out = ps
```

By connecting multiple components this way, a network can be established with packets flowing from packet generators to packet sinks, going through a variety of schedulers, traffic shapers, traffic splitters, and flow demultiplexers.

### Flow identifiers

Flow IDs are assigned to packets when they are generated by a packet generator, which is (optionally) initialized with a specific flow ID. Though this is pretty routine, there is one little catch that one needs to be aware of: we use flow IDs extensively as indices of data structures, such as lists, throughout our framework. For example, in `scheduler/drr.py`, we use flow IDs as indices to look up our lists of deficit counters and quantum values:

```python
self.deficit[flow_id] += self.quantum[flow_id]
```

This is convenient, but it also implies that one cannot use arbitrary flow IDs for the flows going through a network: they must be sequentially generated. Of course, it also implies that these lists will grow larger as flows are established and terminated. Conceptually, one can design a new data structure that maps real flow IDs to indices, and use the mapped indices to look up data structures of *currently active* flows in the network. This, however, adds complexity, which may not be warranted in the current simple design.

