
# %% LIBRARIES
import simpy
import random
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# %% DATA PREPROCESSING

## Bus data
df_bus = pd.read_csv('./bus_service_jueves_SanMames.csv')
df_bus.head()

bus_ts_source = []
for index, data in df_bus.iterrows():
    if (data.hora >= 16) & (data.hora <= 26):
        buses = int(data.buses)
        for i in range(buses):
            ts_source = data.hora*60 + i*(60/buses) - 16*60
            # ts_source = data.hora*60 - 16*60
            bus_ts_source.append(int(ts_source*60))
bus_ts_source = np.array(bus_ts_source)
bus_ts_target = bus_ts_source + 25*60 # estimation
nbus = len(bus_ts_source)

## Agent data
def str2unix(x):
    return pd.to_datetime(x).astype(int) / 10**9

df_agent = pd.read_csv('./arrival_t_espera.csv')
df_agent = df_agent[['id','link_time','scan_time']]
df_agent.scan_time = str2unix(df_agent.scan_time)
df_agent.link_time = str2unix(df_agent.link_time+'+02:00')
df_agent.rename(columns={"link_time": "ts_source", "scan_time": "ts_target"}, inplace=True)

origin = str2unix(['2019-07-11 16:00:00.000+02:00'])[0]
df_agent.ts_source = df_agent.ts_source-origin
df_agent.ts_target = df_agent.ts_target-origin
df_agent['ts_waiting'] = df_agent.ts_target-df_agent.ts_source
df_agent.ts_waiting.hist(bins=100)
df_agent.head()

# %% DATA EXPLORATION
plt.scatter(df_agent.ts_source, df_agent.ts_target, c='red', s=0.1, alpha=0.1)
for x in bus_ts_source:
    plt.axvline(x, lw=0.1)
for y in bus_ts_target:
    plt.axhline(y, lw=0.1)

plt.axvline(bus_ts_source[100], lw=0.1, c='red')
plt.axhline(bus_ts_target[100], lw=0.1, c='red')

# %% DATA PROCESSING
median = df_agent.ts_waiting.quantile(0.5)
qlow = df_agent.ts_waiting.quantile(0.01)
limit = median + (median-qlow) # 4500
df_agent = df_agent[df_agent.ts_waiting < limit].reset_index(drop=True)
df_agent


from sklearn import linear_model
from sklearn.metrics import mean_squared_error, r2_score
regr = linear_model.LinearRegression()
x = df_agent.ts_source.values.reshape(-1,1)
y = df_agent.ts_target.values.reshape(-1,1)
regr.fit(x,y)
y_pred = regr.predict(x)

plt.plot(x,y_pred,c='red')
plt.scatter(x,y,s=1,alpha=0.1)

print('ts_target=' + str(regr.coef_) + '*ts_source + ', str(regr.intercept_))

# %%

# bus_capacity_est = np.repeat(50, nbus)
bus_capacity_est = pd.cut(df_agent.ts_source, bins=bus_ts_source, right=False).value_counts(sort=False).values
bus_capacity_est = np.append(bus_capacity_est, 1)
bus_capacity_est = np.clip(bus_capacity_est, 1, None)

from scipy.signal import savgol_filter
bus_capacity_est_smooth = savgol_filter(bus_capacity_est, 51, 3).astype(int) # window size 51, polynomial order 3
bus_capacity_est_smooth = np.clip(bus_capacity_est_smooth, 1, None)


from scipy.signal import hilbert, chirp
analytic_signal = hilbert(bus_capacity_est)
amplitude_envelope = np.abs(analytic_signal)

plt.plot(bus_capacity_est)
plt.plot(bus_capacity_est_smooth, color='red')
plt.plot(amplitude_envelope, color='green')
plt.show()
# %% SIMULATION

def simulator(data, config):
    assert type(config['GET_ON']) == int
    assert type(config['GET_OFF']) == int
    assert type(config['MONITOR_AT']) == int
    assert type(config['TRAVEL_TIME']) == int
    assert type(config['PATIENCE']) == int
    # assert type(config['BUS_CAPACITY']) == int

    env = simpy.Environment()

    class Bus():
        def __init__(self, env, bus_id, ts_source, bus_capacity):
            self.bus_id = bus_id
            self.env = env
            self.ts_source = ts_source
            self.bus_capacity = bus_capacity

            self.print = False  # control print statemets
            self.bus_is_full = False
            self.driver_out_patience = False

            self.departed_event = self.env.event()  # init departed event
            self.reached_event = self.env.event()  # init reached event
            self.emptied_event = self.env.event()  # init emptied event
            #self.res = None  # init but resource

            self.env.process(self.process())

        # def bus_capacity(self):
        #     from scipy import signal
        #     x = self.env.now
        #     xmean = config['BUS_CAPACITY_mean']
        #     xstd = config['BUS_CAPACITY_std']
        #     h = config['BUS_CAPACITY_height']
        #     b = config['BUS_CAPACITY_min']
        #     if abs(x-xmean) < xstd:
        #         b += h*(1-abs(x-xmean)/xstd)
        #     return b

        def process(self):
            yield self.env.timeout(self.ts_source)  # bus arrival frequency
            if self.print:
                print('Bus %d arriving at %.2f' % (self.bus_id, self.env.now))

            self.res = simpy.Resource(self.env, capacity=self.bus_capacity)  # create bus resource
            self.available_time = self.env.now  # save available time

            yield self.departed_event
            if self.print:
                print('Bus %d departed at %.2f' % (self.bus_id, self.env.now))

            # travel_time = np.random.normal(TRAVEL_TIME, 1)
            yield self.env.timeout(config['TRAVEL_TIME'])  # travel to destination
            self.reached_event.succeed()
            self.ts_reached = self.env.now
            if self.print:
                print('Bus %d reached at %.2f' %
                    (self.bus_id, self.ts_reached))

            yield self.emptied_event
            self.ts_destination = self.env.now
            if self.print:
                print('Bus %d emptied at %.2f' %
                    (self.bus_id, self.ts_destination))


        def available(self):
            if hasattr(self, 'res'):
                return (self.res.count < self.res.capacity) & (not self.departed_event.triggered)
            return False

        def departed(self):
            if hasattr(self, 'res'):
                driver_waiting_time = self.env.now - self.available_time
                driver_out_patience = driver_waiting_time > config['PATIENCE']
                # print('Bus %d count: %d' % (self.bus_id, self.res.count))
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

        def emptied(self):
            if hasattr(self, 'res'):
                return (self.res.count == 0) & (self.departed_event.triggered)
            return False

        def trigger_emptied(self):
            if not self.emptied_event.triggered:
                if self.emptied():
                    self.emptied_event.succeed()
                    self.ts_emptied = self.env.now

        def results(self):
            return {
                'bus_id': self.bus_id,
                'ts_source': self.ts_source,
                'ts_departed': self.ts_departed,
                'ts_reached': self.ts_reached,
                'ts_destination': self.ts_destination,
                'bus_is_full': self.bus_is_full,
                'driver_out_patience': self.driver_out_patience,
            }

    class Agent:
        def __init__(self, env, festival, agent_id, ts_source, ts_target):
            self.env = env
            self.festival = festival
            self.queue_in = self.festival.queue_in
            self.queue_out = self.festival.queue_out
            self.bus_available = self.festival.bus_available
            self.agent_id = agent_id
            self.ts_source = ts_source
            self.ts_target = ts_target

            self.print = False
            self.has_bus = False
            self.env.process(self.process())

        def set_event(self, bus_available):
            self.bus_available = bus_available

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
            if self.print:
                print('Agent %d arriving to queue at %.2f' %
                    (self.agent_id, self.env.now))

        def queue_bus(self):
            # global bus_available
            # print(self.bus_available)
            
            queue_in_request = self.queue_in.request()  # request access to queue
            yield queue_in_request  # wait until turn to board a bus
            yield self.bus_available  # wait until bus is available
            self.ts_bus_available = self.env.now
            yield self.env.timeout(config['GET_ON'])
            self.has_bus = True
            # print(self.agent_id)
            self.bus = self.bus_available.value  # get one available bus
            self.queue_in.release(queue_in_request)  # release queue

            # restart bus_available event
            self.festival.restart_event()


        def join_bus(self):
            self.bus_request = self.bus.res.request()
            yield self.bus_request
            self.ts_bus_joined = self.env.now
            if self.print:
                print('Agent %d on bus %d at %.2f' %
                    (self.agent_id, self.bus.bus_id, self.ts_bus_joined))
            # if self.print: print('Bus %d count: %d' % (self.bus.bus_id, self.bus.res.count))

        def depart_bus(self):
            yield self.bus.departed_event  # check is bus departed
            self.ts_bus_departed = self.env.now

        def travel(self):
            yield self.bus.reached_event
            self.ts_bus_reached = self.env.now
            # self.bus.ts_destination = self.ts_bus_reached
            if self.print:
                print('Agent %d reached destination at %.2f' %
                    (self.agent_id, self.ts_bus_reached))

            queue_out_request = self.queue_out.request()  # request access to queue
            yield queue_out_request  # wait until turn to board a bus
            yield self.env.timeout(config['GET_OFF'])
            self.queue_out.release(queue_out_request)  # release queue

            self.bus.res.release(self.bus_request)

        def finish(self):
            self.ts_destination = self.env.now
            self.ts_simulation = self.ts_destination - self.ts_source
            if self.print:
                print('Agent %d done at %.2f' %
                    (self.agent_id, self.ts_destination))
            if self.print:
                print('Agent %d took %.2f time' %
                    (self.agent_id, self.ts_simulation))

        def results(self):
            if self.has_bus:
                return {
                    'agent_id': self.agent_id,
                    'has_bus': self.has_bus,
                    'bus_id': self.bus.bus_id,
                    'ts_source': self.ts_source,
                    'ts_target': self.ts_target,
                    'ts_bus_available': self.ts_bus_available,
                    'ts_bus_joined': self.ts_bus_joined,
                    'ts_bus_departed': self.ts_bus_departed,
                    'ts_bus_reached': self.ts_bus_reached,
                    'ts_destination': self.ts_destination,
                    'ts_simulation': self.ts_simulation
                }
            else:
                return {
                    'agent_id': self.agent_id,
                    'has_bus': self.has_bus,
                    'bus_id': None,
                    'ts_source': self.ts_source,
                    'ts_target': self.ts_target,
                    'ts_bus_available': None,
                    'ts_bus_joined': None,
                    'ts_bus_departed': None,
                    'ts_bus_reached': None,
                    'ts_destination': None,
                    'ts_simulation': None
                }

    class Festival:

        def __init__(self, env, data):
            self.env = env
            self.queue_in = simpy.Resource(env, capacity=config['QUEUES'])
            self.queue_out = simpy.Resource(env, capacity=config['QUEUES'])
            self.bus_available = env.event()


            # init process data
            self.bus_ts_source = data['bus_ts_source']
            self.agent_ts_source = data['agent_ts_source']
            self.agent_ts_target = data['agent_ts_target']
            self.bus_capacity = data['bus_capacity']

            self.n_buses = len(self.bus_ts_source)
            self.n_agents = len(self.agent_ts_source)

            self.buses = []
            self.agents = []

            # monitor if any bus available
            self.env.process(self.monitor_any_bus_available())
            # monitor if the bus has departed
            self.env.process(self.monitor_bus_departed())
            # monitor if the bus has reached and emptied
            self.env.process(self.monitor_bus_emptied())


            self.init_buses()
            self.init_agents()

        def monitor_any_bus_available(self):
            while True:
                yield self.env.timeout(config['MONITOR_AT'])
                available = any([bus.available() for bus in self.buses])
                if available:
                    if not self.bus_available.triggered:
                        bus = self.select_bus()
                        self.bus_available.succeed(value=bus)
        
        def restart_event(self):
            self.bus_available = self.env.event()
            for agent in self.agents:
                agent.bus_available = self.bus_available

        def select_bus(self):
            # get first available bus seat
            for bus in self.buses:
                if bus.available():
                    return bus

        def monitor_bus_departed(self):
            while True:
                yield self.env.timeout(config['MONITOR_AT'])
                for bus in self.buses:
                    bus.trigger_departed()

        def monitor_bus_emptied(self):
            while True:
                yield self.env.timeout(config['MONITOR_AT'])
                for bus in self.buses:
                    bus.trigger_emptied()

        def init_buses(self):
            for bus_id in range(self.n_buses):
                bus = Bus(self.env, bus_id, self.bus_ts_source[bus_id], self.bus_capacity[bus_id])
                self.buses.append(bus)

        def init_agents(self):
            for agent_id in range(self.n_agents):
                ts_source = self.agent_ts_source[agent_id]
                ts_target = self.agent_ts_target[agent_id]
                # agent = Agent(self.env, self.queue_in, self.queue_out, self.bus_available, 
                #             agent_id, ts_source, ts_target)
                agent = Agent(self.env, self, agent_id, ts_source, ts_target)
                self.agents.append(agent)

    concert = Festival(env, data)
    # env.run(until=3600)
    env.run(until = max(bus_ts_source)+2*3600)
    return concert

def launch(get_off, get_on, monitor_at, patience, travel_time):
    data = {
        'bus_ts_source': bus_ts_source,
        'agent_ts_source': df_agent.ts_source,
        'agent_ts_target': df_agent.ts_target,
        'bus_capacity': bus_capacity_est
    }
    config = {
        'QUEUES' : 1,
        'GET_ON' : int(get_on),
        'GET_OFF' : int(get_off),
        'MONITOR_AT' : int(monitor_at),
        'PATIENCE' : int(patience*60),
        'TRAVEL_TIME' : int(travel_time*60)
    }
    return simulator(data, config), data, config

# %% OPTIMIZATION
def objective(get_off, get_on, monitor_at, patience, travel_time):
    concert, data, config = launch(get_off, get_on, monitor_at, patience, travel_time)

    agents = pd.DataFrame([agent.results() for agent in concert.agents])
    # buses = pd.DataFrame([bus.results() for bus in concert.buses])

    agents['ts_expected'] = agents.ts_target - agents.ts_source
    agents['ts_delta'] = agents.ts_expected - agents.ts_simulation

    rmse = np.sqrt(np.mean(agents.ts_delta**2))
    to_maximise = -rmse
    # print(to_maximise)
    return to_maximise

from bayes_opt import BayesianOptimization
pbounds = {
    'get_off': (0,0),
    'get_on': (0,0),
    'monitor_at': (10,10),
    'patience': (0,60),
    'travel_time': (5,60),
}

optimizer = BayesianOptimization(
    f=objective,
    pbounds=pbounds,
    random_state=1,
    verbose=2,
)
from bayes_opt.observer import JSONLogger
from bayes_opt.event import Events
# logger = JSONLogger(path="./logs.json")
# optimizer.subscribe(Events.OPTMIZATION_STEP, logger)

optimizer.maximize(
    init_points=5,
    n_iter=10,
    alpha=1e-3
)


# %% RESULTS
concert, data, config = launch(0,0,10,32,5)

agents = pd.DataFrame([agent.results() for agent in concert.agents])
# agents.to_csv('agents.csv', index=False, float_format='%.02f')

buses = pd.DataFrame([bus.results() for bus in concert.buses])
# buses.to_csv('buses.csv', index=False, float_format='%.02f')

# %% BUSES ANALYSIS
buses['ts_waiting'] = buses.ts_departed - buses.ts_source
buses['ts_travel'] = buses.ts_reached - buses.ts_departed
buses['ts_total'] = buses.ts_destination - buses.ts_source

fig, ax = plt.subplots(3, 2, figsize=(12,12))
plt.suptitle('Bus Stats \n Config: ' + str(config))

ax[0][0].set_title("bus_is_full histogram")
ax[0][0].hist(buses.bus_is_full.astype(int), bins=2)
ax[0][1].set_title("bus_is_full along ts_source")
ax[0][1].plot(buses.ts_source, buses.bus_is_full)

ax[1][0].set_title("driver_out_patience histogram")
ax[1][0].hist(buses.driver_out_patience.astype(int), bins=2)
ax[1][1].set_title("driver_out_patience along ts_source")
ax[1][1].plot(buses.ts_source, buses.driver_out_patience)


ax[2][0].set_title("ts_waiting histogram")
ax[2][0].hist(buses.ts_waiting, bins=50)
ax[2][1].set_title("ts_total histogram")
ax[2][1].hist(buses.ts_total, bins=50)



# %% AGENTS ANALYSIS
agents['ts_expected'] = agents.ts_target - agents.ts_source
agents['ts_delta'] = agents.ts_expected - agents.ts_simulation

rmse = np.sqrt(np.mean(agents.ts_delta**2))

fig, ax = plt.subplots(2, 2, figsize=(12,10))

plt.suptitle('Agents Stats \n Config: ' + str(config))

ax[0][0].set_title("ts_target")
ax[0][0].hist(agents.ts_source, bins=100, alpha=0.5, label="ts_source")
ax[0][0].hist(agents.ts_target, bins=100, alpha=0.5, label="ts_target")
ax[0][0].legend()

ax[0][1].set_title("ts_destination")
ax[0][1].hist(agents.ts_source, bins=100, alpha=0.5, label="ts_source")
ax[0][1].hist(agents.ts_destination, bins=100, alpha=0.5, label="ts_destination")
ax[0][1].legend()

ax[1][0].set_title("ts_expected vs ts_simulation")
ax[1][0].hist(agents.ts_expected, bins=100, alpha=0.5, label="ts_expected")
ax[1][0].hist(agents.ts_simulation, bins=100, alpha=0.5, label="ts_simulation")
ax[1][0].legend()

ax[1][1].set_title("ts_delta rmse: " + str(int(rmse)))
ax[1][1].hist(agents.ts_delta, bins=100, alpha=0.8, label="ts_delta")


# %%
