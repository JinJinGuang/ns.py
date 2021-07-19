"""
Implements a Static Priority (SP) server.
"""

from collections import defaultdict as dd
from random import random

import simpy
from ns.packet.packet import Packet


class SPServer:
    """
    Parameters
    ----------
    env: simpy.Environment
        The simulation environment.
    rate: float
        The bit rate of the port.
    priorities: list or dict
        This can be either a list or a dictionary. If it is a list, it uses the flow_id
        as its index to look for the flow's corresponding priority. If it is a dictionary,
        it contains (flow_id -> priority) pairs for each possible flow_id.
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
        self.env = env
        self.rate = rate
        self.prio = priorities

        self.stores = {}
        if isinstance(priorities, list):
            self.prio_queue_count = [0 for __ in range(len(priorities))] # count for each flow
        elif isinstance(priorities, dict):
            self.prio_queue_count = {prio: 0 for prio in priorities.values()} # priority -> count
        else:
            raise ValueError(
                'Priorities must be either a list or a dictionary.')

        self.packets_available = simpy.Store(self.env)

        self.current_packet = None

        self.byte_sizes = dd(lambda: 0)

        self.packets_received = 0
        self.out = None
        self.upstream_updates = {}
        self.upstream_stores = {}
        self.zero_buffer = zero_buffer
        self.zero_downstream_buffer = zero_downstream_buffer
        if self.zero_downstream_buffer:
            self.downstream_stores = {}

        self.debug = debug
        self.action = env.process(self.run())

    def update(self, packet):
        """The packet has just been retrieved from this element's own buffer, so
        update internal housekeeping states accordingly."""
        if self.zero_buffer:
            self.upstream_stores[packet].get()
            del self.upstream_stores[packet]
            self.upstream_updates[packet](packet)
            del self.upstream_updates[packet]

        if self.debug:
            print(
                f"Sent out packet {packet.packet_id} of priority {packet.prio}"
            )

        self.prio_queue_count[packet.prio] -= 1

        if packet.flow_id in self.byte_sizes:
            self.byte_sizes[packet.flow_id] -= packet.size
        else:
            raise ValueError("Error: the packet is from an unrecorded flow.")

    def packet_in_service(self) -> Packet:
        """
        Returns the packet that is currently being sent to the downstream element.
        Used by a ServerMonitor.
        """
        return self.current_packet

    def byte_size(self, flow_id) -> int:
        """
        Returns the size of the queue for a particular flow_id, in bytes.
        Used by a ServerMonitor.
        """
        if flow_id in self.byte_sizes:
            return self.byte_sizes[flow_id]

        return 0

    def size(self, flow_id) -> int:
        """
        Returns the size of the queue for a particular flow_id, in the
        number of packets. Used by a ServerMonitor.
        """
        if flow_id in self.stores:
            return len(self.stores[flow_id].items)

        return 0

    def all_flows(self) -> list:
        """
        Returns a list containing all the flow IDs.
        """
        return self.byte_sizes.keys()

    def total_packets(self) -> int:
        if isinstance(self.prio, list):
            return sum(self.prio_queue_count)
        else:
            return sum(self.prio_queue_count.values())

    def run(self):
        """The generator function used in simulations."""
        while True:
            if isinstance(self.prio, list):
                prio_queue_counts = enumerate(self.prio_queue_count)
            else:
                prio_queue_counts = self.prio_queue_count.items()

            for prio, count in prio_queue_counts:
                if count > 0:
                    if self.zero_downstream_buffer:
                        ds_store = self.downstream_stores[prio]
                        packet = yield ds_store.get()
                        packet.prio = prio

                        self.current_packet = packet
                        yield self.env.timeout(packet.size * 8.0 / self.rate)

                        self.out.put(packet,
                                     upstream_update=self.update,
                                     upstream_store=self.stores[prio])
                        self.current_packet = None
                    else:
                        store = self.stores[prio]
                        packet = yield store.get()
                        packet.prio = prio
                        self.update(packet)

                        self.current_packet = packet
                        yield self.env.timeout(packet.size * 8.0 / self.rate)
                        self.out.put(packet)
                        self.current_packet = None

                    break

            if self.total_packets() == 0:
                yield self.packets_available.get()

    def put(self, packet, upstream_update=None, upstream_store=None):
        """ Sends a packet to this element. """ # receive the packet
        self.packets_received += 1
        self.byte_sizes[packet.flow_id] += packet.size

        if self.total_packets() == 0: # if idle？??
            self.packets_available.put(True)

        prio = self.prio[packet.flow_id] # the priority of the flow
        print(self.prio_queue_count)
        print(prio)
        self.prio_queue_count[prio] += 1 # There may be a bug for the LIST version for priority. 

        if self.debug:
            print(
                f"Time {self.env.now}, flow_id {packet.flow_id}, packet_id {packet.packet_id}"
            )

        if not prio in self.stores:
            self.stores[prio] = simpy.Store(self.env) # create a queue for the priority.

            if self.zero_downstream_buffer:
                self.downstream_stores[prio] = simpy.Store(self.env)

        if self.zero_buffer and upstream_update is not None and upstream_store is not None:
            self.upstream_stores[packet] = upstream_store
            self.upstream_updates[packet] = upstream_update

        if self.zero_downstream_buffer:
            self.downstream_stores[prio].put(packet)

        return self.stores[prio].put(packet)



if __name__ == '__main__':
    from ns.packet.dist_generator import DistPacketGenerator
    from ns.packet.sink import PacketSink
    import numpy as np
    np.random.seed(42)

    def arrival_1():
        """ Packets arrive with a constant interval of 1.5 seconds. """
        return 1.5


    def arrival_2():
        """ Packets arrive with a constant interval of 2.0 seconds. """
        return 2.0

    def packet_size():
        return int(np.random.exponential(100))

    DEBUG = True

    env = simpy.Environment()
    # sp = SPServer(env, 100, [1,100], debug=DEBUG)
    # sp = SPServer(env, 100, {0:10, 1:1}, debug=DEBUG)
    sp = SPServer(env, 100, {0:1, 1:10}, debug=DEBUG)
    ps = PacketSink(env, rec_flow_ids=False, debug=DEBUG)

    pg1 = DistPacketGenerator(env, "flow_1", arrival_1, packet_size, flow_id=0)
    pg2 = DistPacketGenerator(env, "flow_2", arrival_2, packet_size, flow_id=1)

    pg1.out = sp
    pg2.out = sp
    sp.out = ps

    env.run(until=20)
