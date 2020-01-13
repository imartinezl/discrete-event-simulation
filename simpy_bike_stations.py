
# %%
import simpy
import random
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

RANDOM_SEED = 42
random.seed(RANDOM_SEED)

WALK_RADIUS = 50

data = {
    'grid': {
        'xlim': [0, 100],
        'ylim': [0, 100]
    },
    'stations': [
        {
            'location': [5, 5],
            'capacity': 3
        },
        {
            'location': [10, 10],
            'capacity': 3
        },
        {
            'location': [90, 90],
            'capacity': 2
        },
        {
            'location': [95, 95],
            'capacity': 2
        }
    ],
    'bikes': [
        {'station': 0},
        {'station': 1},
        {'station': 2},
        {'station': 3},
    ],
    'nagents': 1,
}


class City:
    def __init__(self, env, data):
        self.env = env
        self.data = data

        # self.n_stations = len(self.data['stations'])
        # self.n_bikes = len(self.data['bikes'])
        # self.n_agents = self.data['nagents']
        self.stations = []
        self.bikes = []
        self.agents = []

        self.start()

    def start(self):
        self.init_stations()
        self.init_bikes()
        self.init_agents()

    def init_stations(self):
        for station_id, station_data in enumerate(self.data['stations']):
            station = Station(self.env, station_id)
            station.set_data(station_data)
            station.init_station()
            self.stations.append(station)

    def init_bikes(self):
        for bike_id, bike_data in enumerate(self.data['bikes']):
            bike = Bike(self.env, bike_id)
            station_id = bike_data['station']
            bike.set_station(station_id)  # assign bike to station
            self.stations[station_id].push_bike(bike_id)
            self.stations[station_id].print_info()
            self.bikes.append(bike)

    def init_agents(self):
        for agent_id in range(self.data['nagents']):
            agent = Agent(self.env, agent_id)
            agent.set_data(self.data['grid'], self.stations, self.bikes)
            agent.start()
            self.agents.append(agent)


class Station:

    def __init__(self, env, station_id):
        self.env = env
        self.station_id = station_id
        
        self.location = None
        self.capacity = None
        self.bikes = []
        
        self.history = []

    def init_station(self):
        self.resource = simpy.Resource(self.env, capacity=1)
        self.container = simpy.Container(self.env, self.capacity, init=0)

    def set_data(self, data):
        self.location = np.array(data['location'])
        self.capacity = data['capacity']

    def has_bikes(self):
        return self.container.level > 0

    def has_docks(self):
        return self.capacity - self.container.level > 0

    def empty(self):
        return self.container.level == 0

    def full(self):
        return self.container.level == self.capacity

    def choose_bike(self):
        return random.choice(self.bikes)

    def pull_bike(self, bike_id):
        self.bikes.remove(bike_id)
        self.container.get(1)
        self.save_state()

    def push_bike(self, bike_id):
        self.bikes.append(bike_id)
        self.container.put(1)
        self.save_state()

    def save_state(self):
        # print(self.station_id, np.round(self.env.now), self.bikes, len(self.bikes))
        state = {
            'time': np.round(self.env.now),
            'bikes': self.bikes.copy(), 
            'nbikes': len(self.bikes)
        }
        self.history.append(state)

    def print_info(self):
        print('[%.2f] Station %d has %d bikes out of %d' %
              (self.env.now, self.station_id, self.container.level, self.capacity))


class Bike:
    def __init__(self, env, bike_id):
        self.env = env
        self.bike_id = bike_id

        self.station_id = None
        self.agent_id = None
        self.location = None

        self.state = {}
        self.history = []

    def set_station(self, station_id):
        self.station_id = station_id

    def set_agent(self, agent_id):
        self.agent_id = agent_id

    def set_location(self, location):
        self.location = location

    def pop_station(self):
        self.station_id = None

    def pop_agent(self):
        self.agent_id = None

    def register_pull(self, agent_id):
        self.state['agent_id'] = agent_id
        self.state['station_pull'] = self.station_id
        self.state['time_pull'] = np.round(self.env.now,2)
        self.set_agent(agent_id)
        self.pop_station()

    def register_push(self, station_id):
        self.state['station_push'] = station_id
        self.state['time_push'] = np.round(self.env.now,2)
        self.save_state()
        self.pop_agent()
        self.set_station(station_id)

    def docked(self):
        return self.station_id is not None

    def rented(self):
        return self.agent_id is not None
    
    def vacant(self):
        return self.docked() or not self.rented()

    def dist(self, a, b):
        return np.linalg.norm(a - b)

    def call(self, agent_id):
        self.set_agent(agent_id)
        self.state['agent_id'] = agent_id
        self.state['time_call'] = np.round(self.env.now,2)
        self.state['location_call'] = self.location

    def autonomous_move(self, location):
        distance = self.dist(self.location, location)
        yield self.env.timeout(distance)
        self.location = location
        self.state['location_meet'] = self.location
        self.state['time_meet'] = np.round(self.env.now,2)

    def ride(self, location):
        distance = self.dist(self.location, location)
        yield self.env.timeout(distance)
        self.location = location
        self.state['location_drop'] = self.location
        self.state['time_drop'] = np.round(self.env.now,2)

    def drop(self):
        self.pop_agent()
        self.save_state()

    def save_state(self):
        self.history.append(self.state)
        self.state = {}


class Agent:

    def __init__(self, env, agent_id):
        self.env = env
        self.agent_id = agent_id
        self.grid = None
        self.stations = None
        self.bikes = None

        self.print = True
        self.history = []

        self.count = 0

    def set_data(self, grid, stations, bikes):
        self.grid = grid
        self.stations = stations
        self.bikes = bikes
    
    def start(self):

        self.location = None
        self.bike_id = None
        self.source_station_id = None
        self.target_station_id = None
        self.visited_source_stations = []
        self.visited_target_stations = []      

        self.source_history = []
        self.target_history = []

        self.event_setup_task = self.env.event()
        self.event_select_source_station = self.env.event()
        self.event_select_target_station = self.env.event()
        self.event_pull_bike = self.env.event()
        self.event_push_bike = self.env.event()

        self.env.process(self.process())

    def process(self):
        # 0-Setup
        self.setup_task()
        yield self.event_setup_task

        # 1-Init on source
        yield self.env.process(self.init_agent())

        while not self.event_pull_bike.triggered:
            # 2-Select source station
            self.select_source_station()

            # 3-Walk to source station
            yield self.event_select_source_station
            yield self.env.process(self.walk_to_source_station())

            # 4-Pull bike
            yield self.env.process(self.pull_bike())
            self.save_source_history()

        while not self.event_push_bike.triggered:
            # 5-Select target station
            self.select_target_station()

            # self.stations[3].push_bike(-1)
            
            # 6-Ride bike
            yield self.event_select_target_station
            yield self.env.process(self.ride_bike())

            # 7-Push bike
            yield self.env.process(self.push_bike())
            self.save_target_history()


        # 8-Walk to target
        yield self.env.process(self.walk_to_target())

        # 9-Save state
        self.save_state()
        
        yield self.env.timeout(10)
        if self.print:
            print('[%.2f] Agent %d working' % (self.env.now, self.agent_id))

        self.count += 1
        if self.count < 2:
            self.start()

    def random_location(self):
        x = np.random.randint(*self.grid['xlim'])
        y = np.random.randint(*self.grid['ylim'])
        return np.array([x, y])

    def random_time(self):
        return 10

    def setup_task(self):
        self.source = self.random_location()
        self.target = self.random_location()

        self.source = np.array([0, 0])
        self.target = np.array([100, 100])

        self.time_source = np.round(self.random_time(),2)
        self.time_target_desired = np.round(self.time_source + self.random_time(),2)

        self.event_setup_task.succeed()

        if self.print:
            print('[%.2f] Agent %d task created' %
                  (self.env.now, self.agent_id))
            print('[%.2f] Agent %d source location: (%.2f, %.2f) at %.2f' %
                  (self.env.now, self.agent_id, *self.source, self.time_source))
            print('[%.2f] Agent %d target location: (%.2f, %.2f) at %.2f' %
                  (self.env.now, self.agent_id, *self.target, self.time_target_desired))

    def init_agent(self):
        yield self.env.timeout(self.time_source)
        self.location = self.source
        if self.print:
            print('[%.2f] Agent %d initialized at source [%.2f, %.2f]' %
                  (self.env.now, self.agent_id, *self.source))

    def dist(self, a, b):
        return np.linalg.norm(a - b)

    def current_station_info(self):
        values = []
        for station in self.stations:
            station_id = station.station_id
            has_bikes = station.has_bikes()
            has_docks = station.has_docks()
            visited_source = station_id in self.visited_source_stations
            distance_source = self.dist(self.source, station.location)
            walkable_source = distance_source < WALK_RADIUS
            visited_target = station_id in self.visited_target_stations
            distance_target = self.dist(self.target, station.location)
            walkable_target = distance_target < WALK_RADIUS
            values.append((station_id, has_bikes, has_docks,
                           visited_source, distance_source, walkable_source,
                           visited_target, distance_target, walkable_target))
        labels = ['station_id', 'has_bikes', 'has_docks',
                  'visited_source', 'distance_source', 'walkable_source',
                  'visited_target', 'distance_target', 'walkable_target']
        types = [int, int, int,
                 int, float, int,
                 int, float, int]
        dtype = list(zip(labels, types))
        self.station_info = np.array(values, dtype=dtype)

    def select_source_station(self):
        self.event_select_source_station = self.env.event()
        self.current_station_info()
        for e in np.sort(self.station_info, order='distance_source'):
            # print(e)
            valid = e['has_bikes'] and not e['visited_source'] and e['walkable_source']
            if valid:
                self.source_station_id = e['station_id']
                self.visited_source_stations.append(self.source_station_id)
                self.event_select_source_station.succeed()
                self.time_select_source_station = np.round(self.env.now,2)
                if self.print:
                    print('[%.2f] Agent %d selected source station %d' %
                          (self.env.now, self.agent_id, self.source_station_id))
                break

    def walk_to_source_station(self):
        source_station = self.stations[self.source_station_id]
        distance = self.dist(self.location, source_station.location)
        yield self.env.timeout(distance)
        self.location = source_station.location
        self.time_source_station = np.round(self.env.now,2)

        if self.print:
            print('[%.2f] Agent %d walked to source station %d' %
                  (self.env.now, self.agent_id, self.source_station_id))

    def pull_bike(self):
        source_station = self.stations[self.source_station_id]
        if source_station.has_bikes():
            self.bike_id = source_station.choose_bike()
            self.bikes[self.bike_id].register_pull(self.agent_id)
            source_station.pull_bike(self.bike_id)
            yield self.env.timeout(1)
            self.event_pull_bike.succeed()
            self.time_pull_bike = np.round(self.env.now,2)
            if self.print:
                print('[%.2f] Agent %d pulled bike %d on station %d' %
                      (self.env.now, self.agent_id, self.bike_id, self.source_station_id))
                source_station.print_info()
        else:
            yield self.env.timeout(3)
            self.time_pull_bike = None
            if self.print:
                print('[%.2f] Station %d has zero bikes available' %
                      (self.env.now, self.source_station_id))

    def select_target_station(self):
        self.event_select_target_station = self.env.event()
        self.current_station_info()
        for e in np.sort(self.station_info, order='distance_target'):
            # print(e)
            valid = e['has_docks'] and not e['visited_target'] and e['walkable_target']
            if valid:
                self.target_station_id = e['station_id']
                self.visited_target_stations.append(self.target_station_id)
                self.event_select_target_station.succeed()
                self.time_select_source_station = np.round(self.env.now,2)
                if self.print:
                    print('[%.2f] Agent %d selected target station %d' %
                          (self.env.now, self.agent_id, self.target_station_id))
                break

    def ride_bike(self):
        target_station = self.stations[self.target_station_id]

        distance = self.dist(self.location, target_station.location)
        if self.print:
            print('[%.2f] Agent %d heads from station %d to station %d on bike %d' %
                  (self.env.now, self.agent_id, self.source_station_id, self.target_station_id, self.bike_id))

        yield self.env.timeout(distance)
        self.location = target_station.location
        self.time_target_station = np.round(self.env.now,2)

        if self.print:
            print('[%.2f] Agent %d reaches from station %d to station %d on bike %d' %
                  (self.env.now, self.agent_id, self.source_station_id, self.target_station_id, self.bike_id))

    def push_bike(self):
        target_station = self.stations[self.target_station_id]
        if target_station.has_docks():
            target_station.push_bike(self.bike_id)
            self.bikes[self.bike_id].register_push(self.target_station_id)
            yield self.env.timeout(1)
            self.event_push_bike.succeed()
            self.time_push_bike = np.round(self.env.now,2)
            if self.print:
                print('[%.2f] Agent %d pushed bike %d on station %d' %
                      (self.env.now, self.agent_id, self.bike_id, self.target_station_id))
                target_station.print_info()
        else:
            yield self.env.timeout(3)
            self.time_push_bike = None
            if self.print:
                print('[%.2f] Station %d has zero slots available' %
                      (self.env.now, self.target_station_id))

    def walk_to_target(self):
        target_station = self.stations[self.target_station_id]
        distance = self.dist(target_station.location, self.location)
        yield self.env.timeout(distance)
        self.location = self.target
        self.time_target = np.round(self.env.now,2)

        if self.print:
            print('[%.2f] Agent %d walked to target [%.2f, %.2f]' %
                  (self.env.now, self.agent_id, *self.target))

    def save_source_history(self):
        self.source_history.append({
            'source_station_id': self.source_station_id,
            'time_select_source_station': self.time_select_source_station,
            'time_source_station': self.time_source_station,
            'time_pull_bike': self.time_pull_bike
        })

    def save_target_history(self):
        self.target_history.append({
            'target_station_id': self.target_station_id,
            'time_select_target_station': self.time_select_source_station,
            'time_target_station': self.time_target_station,
            'time_push_bike': self.time_push_bike,
        })

    def save_state(self):
        state = {
            'source': self.source.tolist(),
            'target': self.target.tolist(),
            'time_source': self.time_source,
            'time_target': self.time_target,
            'bike': self.bike_id,
            'source_history': self.source_history,
            'target_history': self.target_history
        }
        self.history.append(state)
        

env = simpy.Environment()
city = City(env, data)
env.run(until=1000)


# %%

stations = []
for station_id, station in enumerate(city.stations):
    df = pd.DataFrame(station.history).assign(station_id=station_id)
    stations.append(df)
df_stations = pd.concat(stations).set_index('station_id').reset_index()


bikes = []
for bike_id, bike in enumerate(city.bikes):
    df = pd.DataFrame(bike.history).assign(bike_id=bike_id)
    bikes.append(df)
df_bikes = pd.concat(bikes, sort=False).set_index('bike_id').reset_index()

agents = []
for agent_id, agent in enumerate(city.agents):
    df = pd.DataFrame(agent.history).assign(agent_id=agent_id)
    source_history = pd.concat([pd.DataFrame(s) for s in df.source_history]).reset_index(drop=True)
    target_history = pd.concat([pd.DataFrame(t) for t in df.target_history]).reset_index(drop=True)
    df_extended = pd.concat([df, source_history, target_history], axis=1)
    agents.append(df)
    
df_agents = pd.concat(agents).set_index('agent_id').reset_index()

# %%
