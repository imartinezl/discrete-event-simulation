

# %%
import simpy
import random

QUEUES = 1
PATIENCE = 25
MONITOR_AT = 0.1
BUS_FREQUENCY = 10
TRAVEL_TIME = 5

class Concert:

    def __init__(self, env):
        self.env = env
        self.buses = []
        self.bus_depart = []
        self.available_time = []

        self.queue = simpy.Resource(self.env, capacity=QUEUES)
        self.bus_available = self.env.event()
        self.env.process(self.monitor_any_bus_available())
        self.env.process(self.monitor_bus_depart())
        self.env.process(self.bus_arrival())
        # self.env.process(self.agents_arrival())
        self.agents_arrival_fix()

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

    def bus_arrival(self):
        while True:
            yield self.env.timeout(BUS_FREQUENCY)  # bus arrival frequency
            print('Bus arriving at %d' % (self.env.now))

            res = simpy.Resource(self.env, capacity=4)
            self.buses.append(res)

            bus_depart = self.env.event()
            self.bus_depart.append(bus_depart)

            self.available_time.append(self.env.now)

    def agents_arrival_fix(self):
        for i in range(15):
            self.env.process(self.agent('Agent %d' % i, i*2))

    def agents_arrival(self):
        i = 0
        while True:
            yield self.env.timeout(MONITOR_AT)
            self.env.process(self.agent('Agent %d' % i, i*2))
            i += 1

    def agent(self, name, arrival_time):

        yield self.env.timeout(arrival_time)  # arrival time
        print('%s arriving at %d' % (name, self.env.now))

        queue_request = self.queue.request()  # request access to queue
        yield queue_request  # wait until turn to board a bus
        yield self.bus_available  # wait until bus is available
        self.queue.release(queue_request)  # release queue

        self.bus_available = self.env.event()  # update available event

        bus_id = self.select_bus()  # get one available bus

        bus_request = self.buses[bus_id].request()
        yield bus_request
        print('%s on bus %d at %d' % (name, bus_id, self.env.now))
        # print('Bus %d count: %d' % (bus_id, self.buses[bus_id].count))

        # check is bus departed
        yield self.bus_depart[bus_id]
        yield self.env.timeout(TRAVEL_TIME)  # travel

        print('%s done at %d' % (name, self.env.now))
        print('%s took %d time' % (name, self.env.now-arrival_time))


env = simpy.Environment()
concert = Concert(env)
env.run(until=100)


# %%
