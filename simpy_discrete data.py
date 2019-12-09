

# %%
import simpy
import random
import numpy as np
import pandas as pd

QUEUES = 1
PATIENCE = 25
MONITOR_AT = 0.001
BUS_FREQUENCY = 10
BUS_CAPACITY = 4
TRAVEL_TIME = 5

bus_source_times = [5, 10, 20, 30, 40, 50]
agent_source_times = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
agent_sink_times = [30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40]
data = {
    'bus_source_times': bus_source_times,
    'agent_source_times': agent_source_times,
    'agent_sink_times': agent_sink_times
}


class Concert:

    def __init__(self, env, data):
        self.env = env
        # init process data 
        self.bus_source_times = data['bus_source_times']
        self.agent_source_times = data['agent_source_times']
        self.agent_sink_times = data['agent_sink_times']
        self.buses = []
        self.bus_depart = []
        self.available_time = []
        self.results = []

        self.queue = simpy.Resource(self.env, capacity=QUEUES) # create waiting queue
        self.bus_available = self.env.event() # event for available bus
        self.env.process(self.monitor_any_bus_available()) # monitor if any bus available
        self.env.process(self.monitor_bus_depart()) # monitor if the bus has departed
        self.bus_source() # start bus source
        self.agents_source() # start agents source 

    def monitor_bus_depart(self):
        while True:
            yield self.env.timeout(MONITOR_AT)
            for i in range(len(self.buses)):
                driver_waiting_time = self.env.now - self.available_time[i]
                driver_out_patience = driver_waiting_time > PATIENCE
                bus_is_full = self.buses[i].count == self.buses[i].capacity
                if bus_is_full | driver_out_patience:
                    if not self.bus_depart[i].triggered:
                        self.bus_depart[i].succeed()
                        print('Bus %d leaving at time %d' %
                              (i, self.env.now))

    def monitor_any_bus_available(self):
        while True:
            yield self.env.timeout(MONITOR_AT)
            available = any(
                [True for bus in self.buses if bus.count < bus.capacity])
            if available:
                if not self.bus_available.triggered:
                    self.bus_available.succeed()

    def select_bus(self):
        # get first available bus seat
        for i in range(len(self.buses)):
            if self.buses[i].count < self.buses[i].capacity:
                return i

    def bus_source(self):
        for i in range(len(self.bus_source_times)):
            self.env.process(self.bus(i))

    def bus(self, bus_id):
        source_time = self.bus_source_times[bus_id]
        yield self.env.timeout(source_time)  # bus arrival frequency
        print('Bus %d arriving at %d' % (bus_id, self.env.now))

        res = simpy.Resource(self.env, capacity=BUS_CAPACITY)
        self.buses.append(res)

        bus_depart = self.env.event()
        self.bus_depart.append(bus_depart)

        self.available_time.append(self.env.now)

    def agents_source(self):
        for i in range(len(self.agent_source_times)):
            self.env.process(self.agent(i))

    def agent(self, agent_id):

        source_time = self.agent_source_times[agent_id]
        yield self.env.timeout(source_time)  # arrival time
        print('Agent %d arriving at %d' % (agent_id, self.env.now))

        queue_request = self.queue.request()  # request access to queue
        yield queue_request  # wait until turn to board a bus
        yield self.bus_available  # wait until bus is available
        self.queue.release(queue_request)  # release queue

        self.bus_available = self.env.event()  # update available event

        bus_id = self.select_bus()  # get one available bus

        bus_request = self.buses[bus_id].request()
        yield bus_request
        print('Agent %d on bus %d at %d' % (agent_id, bus_id, self.env.now))
        # print('Bus %d count: %d' % (bus_id, self.buses[bus_id].count))

        
        yield self.bus_depart[bus_id] # check is bus departed
        yield self.env.timeout(TRAVEL_TIME)  # travel to destination

        sink_time = self.agent_sink_times[agent_id]
        simu_time = self.env.now - source_time
        print('Agent %d done at %d' % (agent_id, simu_time))
        print('Agent %d took %d time' % (agent_id, simu_time-source_time))

        r = {
            'id': agent_id,
            'source_time': source_time,
            'sink_time': sink_time,
            'simu_time': np.round(simu_time)
        }
        self.results.append(r)


env = simpy.Environment()
concert = Concert(env, data)
env.run(until=100)

# %%
r = concert.results
pd.DataFrame(r)

# %%
