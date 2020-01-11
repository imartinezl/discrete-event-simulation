
# %%
import simpy
import random
import numpy as np
import pandas as pd

RANDOM_SEED = 42
random.seed(RANDOM_SEED)

WALK_RADIUS = 200

data = {
    'grid': {
        'xlim': [0, 100],
        'ylim': [0, 100]
    },
    'stations': [
        {
            'location': [10, 10],
            'capacity': 5,
            'nbikes': 3
        },
        {
            'location': [90, 90],
            'capacity': 5,
            'nbikes': 3
        }
    ],
    'agents': [
        {
            'age': 18
        },
        # {
        #     'age': 28
        # }
    ]
}


class City:
    def __init__(self, env, data):
        self.env = env
        self.data = data

        # self.n_stations = len(self.data['stations'])
        # self.n_agents = len(self.data['agents'])
        self.stations = []
        self.agents = []

        self.init_stations()
        self.init_bikes()
        self.init_agents()

    def init_stations(self):
        for station_id, station_data in enumerate(self.data['stations']):
            location = station_data['location']
            capacity = station_data['capacity']
            nbikes = station_data['nbikes']
            station = Station(self.env, station_id, location, capacity, nbikes)
            self.stations.append(station)

    def init_bikes(self):
        for station_data in self.data['stations']:
            nbikes = station_data['nbikes']
            for bike_id in range(nbikes):
                bike = Bike(self.env, bike_id, station_id)
                self.bikes.append(bike)

    def init_agents(self):
        for agent_id, agent_data in enumerate(self.agents):
            grid = self.data['grid']
            stations = self.stations
            agent = Agent(self.env, agent_id, grid, stations, None)
            self.agents.append(agent)



class Station:

    def __init__(self, env, station_id, location, capacity, nbikes):
        self.env = env
        self.station_id = station_id
        self.location = np.array(location)
        self.capacity = capacity
        self.nbikes = nbikes

        self.resource = simpy.Resource(self.env, capacity=1)
        self.container = simpy.Container(
            self.env, self.capacity, init=self.nbikes)

    def has_bikes(self):
        return self.container.level > 0

    def has_docks(self):
        return self.capacity - self.container.level > 0

    def empty(self):
        return self.container.level == 0

    def full(self):
        return self.container.level == self.capacity

    def pull_bike(self):
        yield self.container.get(1)

    def push_bike(self):
        yield self.container.put(1)

    def print_info(self):
        print('[%.2f] Station %d has %d bikes out of %d' % 
            (self.env.now, self.station_id, self.container.level, self.capacity))

class Agent:

    def __init__(self, env, agent_id, grid, stations, bikes):
        self.env = env
        self.agent_id = agent_id
        self.grid = grid
        self.stations = stations

        self.print = True
        self.bike_id = None
        self.source_station_id = None
        self.target_station_id = None
        self.checked_source_stations = []
        self.checked_target_stations = []

        self.event_setup_task = self.env.event()
        self.event_select_source_station = self.env.event()
        self.event_select_target_station = self.env.event()

        self.env.process(self.process())

    def process(self):
        self.setup_task()
        yield self.event_setup_task
        yield self.env.process(self.init_agent())

        self.location = self.source
        self.select_source_station()
        yield self.event_select_source_station
        yield self.env.process(self.walk_to_source())
        source_station = self.stations[self.source_station_id]
        self.location = source_station.location
        yield self.env.process(self.pull_bike())
        self.location = self.target
        self.select_target_station()
        yield self.event_select_target_station
        yield self.env.process(self.ride_bike())
        target_station = self.stations[self.target_station_id]
        self.location = target_station.location
        yield self.env.process(self.push_bike())
        yield self.env.process(self.walk_to_target())
        self.location = self.target

        yield self.env.timeout(10)
        if self.print:
            print('[%.2f] Agent %d working' % (self.env.now, self.agent_id))

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

        self.source_ts = self.env.now + self.random_time()
        self.target_ts = self.source_ts + self.random_time()

        self.event_setup_task.succeed()

        if self.print:
            print('[%.2f] Agent %d task created' %
                  (self.env.now, self.agent_id))
            print('[%.2f] Agent %d source location: [%.2f, %.2f] at %.2f' %
                  (self.env.now, self.agent_id, *self.source, self.source_ts))
            print('[%.2f] Agent %d target location: [%.2f, %.2f] at %.2f' %
                  (self.env.now, self.agent_id, *self.target, self.target_ts))

    def init_agent(self):
        yield self.env.timeout(self.source_ts)
        if self.print:
            print('[%.2f] Agent %d initialized at source [%.2f, %.2f]' %
                  (self.env.now, self.agent_id, *self.source))

    def dist(self, a, b):
        return np.linalg.norm(a - b)

    def select_source_station(self):
        values = []
        for station in self.stations:
            station_id = station.station_id
            has_bikes = station.has_bikes()
            distance = self.dist(self.location, station.location)
            walkable = distance < WALK_RADIUS
            visited = station_id in self.checked_target_stations
            values.append((station_id, has_bikes, distance, walkable, visited))
        # labels = ['station_id','has_bikes','distance','walkable','visited']
        # types = [int,bool,float,bool,bool]
        # dtype = list(zip(labels, types))
        dtype = [('station_id', int), ('has_bikes', int),
                 ('distance', float), ('walkable', int), ('visited', int)]
        self.source_station_info = np.array(values, dtype=dtype)
        self.source_station_info_sorted = np.sort(
            self.source_station_info, order='distance')
        for e in self.source_station_info_sorted:
            # print(e)
            valid = e['has_bikes'] and e['walkable'] and not e['visited']
            if valid:
                self.source_station_id = e['station_id']
                self.checked_source_stations.append(self.source_station_id)
                self.event_select_source_station.succeed()
                if self.print:
                    print('[%.2f] Agent %d selected source station %d' %
                          (self.env.now, self.agent_id, self.source_station_id))
                break

    def walk_to_source(self):
        source_station = self.stations[self.source_station_id]
        distance = self.dist(self.location, source_station.location)
        yield self.env.timeout(distance)

        if self.print:
            print('[%.2f] Agent %d walked to source station %d' %
                    (self.env.now, self.agent_id, self.source_station_id))

    def pull_bike(self):
        source_station = self.stations[self.source_station_id]
        if source_station.has_bikes():
            yield self.env.process(source_station.pull_bike())
            # yield self.source_station.container.get(1)
            # yield self.env.timeout(1)
            if self.print:
                print('[%.2f] Agent %d pulled bike on station %d' %
                      (self.env.now, self.agent_id, self.source_station_id))
                source_station.print_info()
        else:
            print("station has zero bikes")

    def select_target_station(self):
        values = []
        for station in self.stations:
            station_id = station.station_id
            has_docks = station.has_docks()
            distance = self.dist(self.location, station.location)
            walkable = distance < WALK_RADIUS
            visited = station_id in self.checked_target_stations
            values.append((station_id, has_docks, distance, walkable, visited))
        # labels = ['station_id','has_docks','distance','walkable','visited']
        # types = [int,bool,float,bool,bool]
        # dtype = list(zip(labels, types))
        dtype = [('station_id', int), ('has_docks', int),
                 ('distance', float), ('walkable', int), ('visited', int)]
        self.target_station_info = np.array(values, dtype=dtype)
        self.target_station_info_sorted = np.sort(
            self.target_station_info, order='distance')
        for e in self.target_station_info_sorted:
            # print(e)
            valid = e['has_docks'] and e['walkable'] and not e['visited']
            if valid:
                self.target_station_id = e['station_id']
                self.checked_target_stations.append(self.target_station_id)
                self.event_select_target_station.succeed()
                if self.print:
                    print('[%.2f] Agent %d selected target station %d' %
                          (self.env.now, self.agent_id, self.target_station_id))
                break

    def ride_bike(self):
        source_station = self.stations[self.source_station_id]
        target_station = self.stations[self.target_station_id]

        distance = self.dist(source_station.location,
                             target_station.location)
        if self.print:
            print('[%.2f] Agent %d heads from station %d to station %d on bike' %
                  (self.env.now, self.agent_id, self.source_station_id, self.target_station_id))
        yield self.env.timeout(distance)
        if self.print:
            print('[%.2f] Agent %d reaches from station %d to station %d on bike' %
                  (self.env.now, self.agent_id, self.source_station_id, self.target_station_id))

    def push_bike(self):
        target_station = self.stations[self.target_station_id]
        if target_station.has_docks():
            yield self.env.process(target_station.push_bike())
            # yield self.target_station.container.put(1)
            # yield self.env.timeout(1)
            if self.print:
                print('[%.2f] Agent %d pushed bike on station %d' %
                      (self.env.now, self.agent_id, self.target_station_id))
                target_station.print_info()
        else:
            print("station has zero docks")

    def walk_to_target(self):
        target_station = self.stations[self.target_station_id]
        distance = self.dist(target_station.location, self.location)
        yield self.env.timeout(distance)
    
        if self.print:
            print('[%.2f] Agent %d walked to target [%.2f, %.2f]' %
                    (self.env.now, self.agent_id, *self.target))

class Bike:
    def __init__(self, env, bike_id):
        self.env = env
        self.bike_id = bike_id
        self.stations = stations
        self.agents = agents

        self.station_id = None
        self.agent_id = None

    def set_station(self, station_id):
        self.station_id = station_id

    def set_agent(self, agent_id):
        self.agent_id = agent_id


env = simpy.Environment()
city = City(env, data)
env.run(until=1000)
