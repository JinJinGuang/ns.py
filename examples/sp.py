import numpy as np
import simpy
from ns.packet.dist_generator import DistPacketGenerator
from ns.packet.sink import PacketSink
from ns.scheduler.sp import SPServer

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
sp = SPServer(env, 100, [1,100], debug=DEBUG) # line[1]
# sp = SPServer(env, 100, {0:10, 1:1}, debug=DEBUG) # line[2]
# sp = SPServer(env, 100, {0:1, 1:10}, debug=DEBUG) # line[3]
ps = PacketSink(env, rec_flow_ids=False, debug=DEBUG)

pg1 = DistPacketGenerator(env, "flow_1", arrival_1, packet_size, flow_id=0)
pg2 = DistPacketGenerator(env, "flow_2", arrival_2, packet_size, flow_id=1)

pg1.out = sp
pg2.out = sp
sp.out = ps

env.run(until=20)
