
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
        'xlim': [0,100],
        'ylim': [0,100]
    },
    'stations': [
        {
            'location': [0,0],
            'capacity': 5,
            'bikes': 3
        },
        {
            'location': [10,10],
            'capacity': 5,
            'bikes': 3
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

        self.n_stations = len(self.data['stations'])
        self.n_agents = len(self.data['agents'])
        self.stations = []
        self.agents = []

        self.init_stations()
        self.init_agents()

    def init_stations(self):
        for station_id in range(self.n_stations):
            location = self.data['stations'][station_id]['location']
            capacity = self.data['stations'][station_id]['capacity']
            bikes = self.data['stations'][station_id]['bikes']
            station = Station(self.env, station_id, location, capacity, bikes)
            self.stations.append(station)

    def init_agents(self):
        for agent_id in range(self.n_agents):
            grid = self.data['grid']
            stations = self.stations
            agent = Agent(self.env, agent_id, grid, stations)
            self.agents.append(agent)

class Station:

    def __init__(self, env, station_id, location, capacity, bikes):
        self.env = env
        self.station_id = station_id
        self.location = location
        self.capacity = capacity
        self.bikes = bikes

        self.resource = simpy.Resource(self.env, capacity=1)
        self.container = simpy.Container(self.env, self.capacity, init=self.bikes)

    def has_bikes(self):
        return self.container.level > 0

    def has_slots(self):
        return self.capacity - self.container.level > 0

    def empty(self):
        return self.container.level == 0

    def full(self):
        return self.container.level == self.capacity


class Agent:

    def __init__(self, env, agent_id, grid, stations):
        self.env = env
        self.agent_id = agent_id
        self.grid = grid
        self.stations = stations

        self.print = True
        self.source_station = None
        self.target_station = None
        self.checked_source_stations = []
        self.checked_target_stations = []

        
        self.env.process(self.process())

    def process(self):
        self.create_task()
        self.select_source_station()
        yield self.env.process(self.walk_to_source())
        
        yield self.env.timeout(10)
        if self.print:
            print('Agent %d working at %.2f' % (self.agent_id, self.env.now))

    def random_location(self):
        x = np.random.randint(*self.grid['xlim'])
        y = np.random.randint(*self.grid['ylim'])
        return np.array([x,y])

    def random_time(self):
        return 100

    def create_task(self):
        self.source = self.random_location()
        self.target = self.random_location()

        self.source_ts = self.env.now + self.random_time()
        self.target_ts = self.source_ts + self.random_time()

        self.location = self.source
        

    def dist(self, a, b):
        return np.linalg.norm(a - b)
    
    # def dist(self, station):
    #     return np.linalg.norm(self.location - station.location)

    

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
        dtype = [('station_id',int),('has_bikes',int),('distance',float),('walkable',int),('visited',int)]
        self.source_station_info = np.array(values, dtype=dtype)
        self.source_station_info_sorted = np.sort(self.source_station_info, order='distance')
        for e in self.source_station_info_sorted:
            print(e)
            valid = e['has_bikes'] and e['walkable'] and not e['visited']
            if valid:
                station_id = e[station_id]
                self.source_station = self.stations[station_id]
                self.checked_source_stations.append(station_id)
                break

                
    def walk_to_source(self):
        if self.source_station is not None:
            distance = self.dist(self.location, self.source_station.location)
            yield self.env.timeout(distance)

    def pull_bike(self):
        if self.source_station.has_bikes():
            yield self.source_station.container.get(1)
            yield self.env.timeout(1)
        else:
            print("station has zero bikes")

    def select_target_station(self):
        values = []
        for station in self.stations:
            station_id = station.station_id
            has_slots = station.has_slots()
            distance = self.dist(self.location, station.location)
            walkable = distance < WALK_RADIUS
            visited = station_id in self.checked_target_stations
            values.append((station_id, has_slots, distance, walkable,visited))
        # labels = ['station_id','has_slots','distance','walkable','visited']
        # types = [int,bool,float,bool,bool]
        # dtype = list(zip(labels, types))
        dtype = [('station_id',int),('has_slots',int),('distance',float),('walkable',int),('visited',int)]
        self.target_station_info = np.array(values, dtype=dtype)
        self.target_station_info_sorted = np.sort(self.target_station_info, order='distance')
        for e in self.target_station_info_sorted:
            print(e)
            valid = e['has_slots'] and e['walkable'] and not e['visited']
            if valid:
                station_id = e[station_id]
                self.target_station = self.stations[station_id]
                self.checked_target_stations.append(station_id)
                break

    def ride_bike(self):
        distance = self.dist(self.source_station.location, self.target_station.location)
        yield self.env.timeout(distance)

    def push_bike(self):
        if self.target_station.has_slots():
            yield self.target_station.container.get(1)
            yield self.env.timeout(1)
        else:
            print("station has zero slots")
    
    def walk_to_target(self):
        if self.target_station is not None:
            distance = self.dist(self.target_station.location, self.location)
            yield self.env.timeout(distance)





        
        


env = simpy.Environment()
city = City(env, data)
env.run(until=100)