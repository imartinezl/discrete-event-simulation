

# %%
import simpy
import random
import numpy as np
import pandas as pd
# from agent import Agent
# from bus import Bus

QUEUES = 1
PATIENCE = 27
MONITOR_AT = 0.1
BUS_FREQUENCY = 10
BUS_CAPACITY = 4
TRAVEL_TIME = 5

bus_ts_source = [5, 10, 20, 30, 40, 50]
agent_ts_source = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
agent_ts_sink = [30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40]
data = {
    'bus_ts_source': bus_ts_source,
    'agent_ts_source': agent_ts_source,
    'agent_ts_sink': agent_ts_sink
}

env = simpy.Environment()
bus_available = env.event()

class Bus():
    def __init__(self, env, bus_id, ts_source):
        self.bus_id = bus_id
        self.env = env
        self.ts_source = ts_source

        self.print = False # control print statemets
        self.bus_is_full = False
        self.driver_out_patience = False
        self.departed_event = self.env.event() # init departed event
        self.res = None # init but resource

        self.env.process(self.process())

    def process(self):
        yield self.env.timeout(self.ts_source)  # bus arrival frequency
        if self.print: print('Bus %d arriving at %.2f' % (self.bus_id, self.env.now))

        self.res = simpy.Resource(self.env, capacity=BUS_CAPACITY) # create bus resource
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
            self.driver_out_patience = driver_out_patience
            self.bus_is_full = bus_is_full
            return bus_is_full | driver_out_patience
        return False
        
    def trigger_departed(self):
        if not self.departed_event.triggered:
            if self.departed():
                self.departed_event.succeed()
                self.ts_departed = self.env.now
                if self.print: print('Bus %d leaving at time %.2f' % (self.bus_id, self.ts_departed))

    def results(self):
        return {
            'bus_id': self.bus_id,
            'ts_source': self.ts_source,
            'ts_departed': self.ts_departed,
            'bus_is_full': self.bus_is_full,
            'driver_out_patience': self.driver_out_patience,
        }

class Agent:
    def __init__(self, env, queue, agent_id, ts_source):
        self.env = env
        self.queue = queue
        self.agent_id = agent_id
        self.ts_source = ts_source
        self.print = False

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
        yield self.env.timeout(self.ts_source)  # arrival time
        if self.print: print('Agent %d arriving to queue at %.2f' % (self.agent_id, self.env.now))

    def queue_bus(self):
        global bus_available

        queue_request = self.queue.request()  # request access to queue
        yield queue_request  # wait until turn to board a bus
        yield bus_available  # wait until bus is available
        self.bus = bus_available.value # get one available bus
        self.queue.release(queue_request)  # release queue
        bus_available = self.env.event()  # restart bus_available event
        self.ts_bus_available = self.env.now

    def join_bus(self):
        bus_request = self.bus.res.request()
        yield bus_request
        self.ts_bus_joined = self.env.now
        if self.print: print('Agent %d on bus %d at %.2f' % (self.agent_id, self.bus.bus_id, self.ts_bus_joined))
        # if self.print: print('Bus %d count: %d' % (self.bus.bus_id, self.bus.res.count))

    def depart_bus(self):
        yield self.bus.departed_event # check is bus departed
        self.ts_bus_departed = self.env.now

    def travel(self):
        travel_time = np.random.normal(TRAVEL_TIME, 1)
        yield self.env.timeout(travel_time)  # travel to destination
        self.ts_destination = self.env.now

    def finish(self):
        self.ts_simulation = self.ts_destination - self.ts_source
        if self.print: print('Agent %d done at %.2f' % (self.agent_id, self.ts_destination))
        if self.print: print('Agent %d took %.2f time' % (self.agent_id, self.ts_simulation))

    def results(self):
        return {
            'agent_id': self.agent_id,
            'ts_source': self.ts_source,
            'ts_bus_available': self.ts_bus_available,
            'ts_bus_joined': self.ts_bus_joined,
            'ts_bus_departed': self.ts_bus_departed,
            'ts_destination': self.ts_destination,
            'ts_simulation': self.ts_simulation            
        }
        
class Concert:

    def __init__(self, env, data):
        self.env = env
        self.queue = simpy.Resource(env, capacity=QUEUES)

        # init process data 
        self.bus_ts_source = data['bus_ts_source']
        self.agent_ts_source = data['agent_ts_source']
        # self.agent_ts_sink = data['agent_ts_sink']

        self.n_buses = len(self.bus_ts_source)
        self.n_agents = len(self.agent_ts_source)

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
            bus = Bus(self.env, bus_id, self.bus_ts_source[bus_id])
            self.buses.append(bus)

    def init_agents(self):
        for agent_id in range(self.n_agents):
            ts_source = self.agent_ts_source[agent_id]
            # sink_time = self.agent_sink_times[agent_id]
            agent = Agent(self.env, self.queue, agent_id, ts_source)
            self.agents.append(agent)

concert = Concert(env, data)
env.run(until=100)


# %%

agents = pd.DataFrame([agent.results() for agent in concert.agents])
agents
# %%
bus = pd.DataFrame([bus.results() for bus in concert.buses])
bus

# %%
