
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
            'capacity': 5
        },
        {
            'location': [90, 90],
            'capacity': 5
        }
    ],
    'bikes': [
        {'station': 0},
        {'station': 0},
        {'station': 0},
        {'station': 1},
        {'station': 1},
        {'station': 1},
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
            self.agents.append(agent)


class Station:

    def __init__(self, env, station_id):
        self.env = env
        self.station_id = station_id
        self.location = None
        self.capacity = None
        self.bikes = []

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

    def push_bike(self, bike_id):
        self.bikes.append(bike_id)
        self.container.put(1)

    def print_info(self):
        print('[%.2f] Station %d has %d bikes out of %d' %
              (self.env.now, self.station_id, self.container.level, self.capacity))


class Bike:
    def __init__(self, env, bike_id):
        self.env = env
        self.bike_id = bike_id

        self.station_id = None
        self.agent_id = None

    def set_station(self, station_id):
        self.station_id = station_id

    def set_agent(self, agent_id):
        self.agent_id = agent_id


class Agent:

    def __init__(self, env, agent_id):
        self.env = env
        self.agent_id = agent_id
        self.grid = None
        self.stations = None
        self.bikes = None

        self.print = True
        self.location = None
        self.bike_id = None
        self.source_station_id = None
        self.target_station_id = None
        self.visited_source_stations = []
        self.visited_target_stations = []

        self.event_setup_task = self.env.event()
        self.event_select_source_station = self.env.event()
        self.event_select_target_station = self.env.event()

        self.env.process(self.process())

    def set_data(self, grid, stations, bikes):
        self.grid = grid
        self.stations = stations
        self.bikes = bikes

    def process(self):
        # 0-Setup
        self.setup_task()
        yield self.event_setup_task

        # 1-Init on source
        yield self.env.process(self.init_agent())

        # 2-Select source station
        self.select_source_station()

        # 3-Walk to source station
        yield self.event_select_source_station
        yield self.env.process(self.walk_to_source_station())

        # 4-Pull bike
        yield self.env.process(self.pull_bike())

        # 5-Select target station
        self.select_target_station()
        yield self.event_select_target_station

        # 6-Ride bike
        yield self.env.process(self.ride_bike())

        # 7-Push bike
        yield self.env.process(self.push_bike())

        # 8-Walk to target
        yield self.env.process(self.walk_to_target())
        
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
            print('[%.2f] Agent %d source location: (%.2f, %.2f) at %.2f' %
                  (self.env.now, self.agent_id, *self.source, self.source_ts))
            print('[%.2f] Agent %d target location: (%.2f, %.2f) at %.2f' %
                  (self.env.now, self.agent_id, *self.target, self.target_ts))

    def init_agent(self):
        yield self.env.timeout(self.source_ts)
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
        self.current_station_info()
        for e in np.sort(self.station_info, order='distance_source'):
            valid = e['has_bikes'] and not e['visited_source'] and e['walkable_source']
            if valid:
                self.source_station_id = e['station_id']
                self.visited_source_stations.append(self.source_station_id)
                self.event_select_source_station.succeed()
                if self.print:
                    print('[%.2f] Agent %d selected source station %d' %
                          (self.env.now, self.agent_id, self.source_station_id))
                break

    def walk_to_source_station(self):
        source_station = self.stations[self.source_station_id]
        distance = self.dist(self.location, source_station.location)
        yield self.env.timeout(distance)
        self.location = source_station.location

        if self.print:
            print('[%.2f] Agent %d walked to source station %d' %
                  (self.env.now, self.agent_id, self.source_station_id))

    def pull_bike(self):
        source_station = self.stations[self.source_station_id]
        if source_station.has_bikes():
            self.bike_id = source_station.choose_bike()
            source_station.pull_bike(self.bike_id)
            yield self.env.timeout(1)
            if self.print:
                print('[%.2f] Agent %d pulled bike %d on station %d' %
                      (self.env.now, self.agent_id, self.bike_id, self.source_station_id))
                source_station.print_info()
        else:
            print("station has zero bikes")

    def select_target_station(self):
        self.current_station_info()
        for e in np.sort(self.station_info, order='distance_target'):
            # print(e)
            valid = e['has_docks'] and not e['visited_target'] and e['walkable_target']
            if valid:
                self.target_station_id = e['station_id']
                self.visited_target_stations.append(self.target_station_id)
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
            print('[%.2f] Agent %d heads from station %d to station %d on bike %d' %
                  (self.env.now, self.agent_id, self.source_station_id, self.target_station_id, self.bike_id))

        yield self.env.timeout(distance)
        self.location = target_station.location

        if self.print:
            print('[%.2f] Agent %d reaches from station %d to station %d on bike %d' %
                  (self.env.now, self.agent_id, self.source_station_id, self.target_station_id, self.bike_id))

    def push_bike(self):
        target_station = self.stations[self.target_station_id]
        if target_station.has_docks():
            target_station.push_bike(self.bike_id)
            yield self.env.timeout(1)
            if self.print:
                print('[%.2f] Agent %d pushed bike %d on station %d' %
                      (self.env.now, self.agent_id, self.bike_id, self.target_station_id))
                target_station.print_info()
        else:
            print("station has zero docks")

    def walk_to_target(self):
        target_station = self.stations[self.target_station_id]
        distance = self.dist(target_station.location, self.location)
        yield self.env.timeout(distance)
        self.location = self.target

        if self.print:
            print('[%.2f] Agent %d walked to target [%.2f, %.2f]' %
                  (self.env.now, self.agent_id, *self.target))


env = simpy.Environment()
city = City(env, data)
env.run(until=1000)
