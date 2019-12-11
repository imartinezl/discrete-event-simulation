

# %%
import simpy
import random
import numpy as np
import pandas as pd
# from agent import Agent
# from bus import Bus

QUEUES = 1
PATIENCE = 27
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

env = simpy.Environment()
bus_available = env.event()

class Bus():
    def __init__(self, env, bus_id, source_time):
        self.bus_id = bus_id
        self.env = env
        self.source_time = source_time

        self.res = None
        self.env.process(self.process())

    def process(self):
        yield self.env.timeout(self.source_time)  # bus arrival frequency
        print('Bus %d arriving at %d' % (self.bus_id, self.env.now))

        self.res = simpy.Resource(self.env, capacity=BUS_CAPACITY) # create bus resource
        self.departed_event = self.env.event() # init departed event
        self.available_time = self.env.now # save available time

    def available(self):
        if self.res:
            return self.res.count < self.res.capacity
        return False

    def departed(self):
        if self.res:
            driver_waiting_time = self.env.now - self.available_time
            driver_out_patience = driver_waiting_time > PATIENCE
            bus_is_full = self.res.count == self.res.capacity
            return bus_is_full | driver_out_patience
        return False
        
    def trigger_departed(self):
        if self.departed():
            if not self.departed_event.triggered:
                self.departed_event.succeed()
                print('Bus %d leaving at time %d' % (self.bus_id, self.env.now))

class Agent:
    def __init__(self, env, queue, agent_id, source_time, sink_time):
        self.env = env
        self.queue = queue
        self.agent_id = agent_id
        self.source_time = source_time
        self.sink_time = sink_time

        self.env.process(self.process())
   
    def process(self):
        yield env.process(self.arrival())
        yield env.process(self.queue_bus())
        yield env.process(self.join_bus())
        yield env.process(self.depart_bus())
        yield env.process(self.travel())
        self.finish()
        pass

    def arrival(self):
        yield self.env.timeout(self.source_time)  # arrival time
        print('Agent %d arriving at %d' % (self.agent_id, self.env.now))

    def queue_bus(self):
        global bus_available

        queue_request = self.queue.request()  # request access to queue
        yield queue_request  # wait until turn to board a bus
        yield bus_available  # wait until bus is available
        self.bus = bus_available.value # get one available bus
        self.queue.release(queue_request)  # release queue
        bus_available = self.env.event()  # restart bus_available event

    def join_bus(self):
        bus_request = self.bus.res.request()
        yield bus_request
        print('Agent %d on bus %d at %d' % (self.agent_id, self.bus.bus_id, self.env.now))
        # print('Bus %d count: %d' % (self.bus.bus_id, self.bus.res.count))

    def depart_bus(self):
        yield self.bus.departed_event # check is bus departed

    def travel(self):
        yield self.env.timeout(TRAVEL_TIME)  # travel to destination

    def finish(self):
        self.stop_time = self.env.now
        self.simu_time = self.stop_time - self.source_time
        print('Agent %d done at %d' % (self.agent_id, self.stop_time))
        print('Agent %d took %d time' % (self.agent_id, self.simu_time))

        


class Concert:

    def __init__(self, env, data):
        self.env = env
        self.queue = simpy.Resource(env, capacity=QUEUES)


        # init process data 
        self.bus_source_times = data['bus_source_times']
        self.agent_source_times = data['agent_source_times']
        self.agent_sink_times = data['agent_sink_times']

        self.n_buses = len(self.bus_source_times)
        self.n_agents = len(self.agent_source_times)

        self.buses = []
        self.agents = []

        self.env.process(self.monitor_any_bus_available())  # monitor if any bus available
        self.env.process(self.monitor_bus_departed()) # monitor if the bus has departed

        self.init_buses()
        self.init_agents()
    
    def monitor_any_bus_available(self):
        while True:
            yield self.env.timeout(MONITOR_AT)
            available = any([bus.available() for bus in self.buses])
            if available:
                if not bus_available.triggered:
                    bus = self.select_bus()
                    bus_available.succeed(value=bus)
    
    def select_bus(self):
        # get first available bus seat
        for bus in self.buses:
            if bus.available():
                return bus

    def monitor_bus_departed(self):
        while True:
            yield self.env.timeout(MONITOR_AT)
            for bus in self.buses:
                bus.trigger_departed()

    def init_buses(self):
        for bus_id in range(self.n_buses):
            bus = Bus(self.env, bus_id, self.bus_source_times[bus_id])
            self.buses.append(bus)

    def init_agents(self):
        for agent_id in range(self.n_agents):
            source_time = self.agent_source_times[agent_id]
            sink_time = self.agent_sink_times[agent_id]
            agent = Agent(self.env, self.queue, agent_id, source_time, sink_time)
            self.agents.append(agent)

concert = Concert(env, data)
env.run(until=100)


# %%
