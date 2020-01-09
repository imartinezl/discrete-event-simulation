
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

    def available(self):
        return self.container.level > 0

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

        self.create_task()
        self.select_source_station()
        # print(self.source, self.target, self.source_ts, self.target_ts)
        self.env.process(self.process())

    def process(self):
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

    def dist(self, station):
        return np.linalg.norm(self.location - station.location)

    

    def select_source_station(self):
        values = []
        for station in self.stations:
            station_id = station.station_id
            available = station.available()
            distance = self.dist(station)
            walkable = distance < WALK_RADIUS
            visited = station_id in self.checked_source_stations
            values.append((station_id, available, distance, walkable,visited))
        labels = ['station_id','available','distance','walkable','visited']
        types = [int,bool,float,bool,bool]
        dtype = [('station_id',int),('available',bool),('distance',float),('walkable',bool),('visited',bool)]
        self.a = np.array(values, dtype=list(zip(labels,types)))
        self.a = np.sort(self.a, order='distance')
        for e in self.a:
            print(e, e.available)
        #     if e.available and e.walkable and not e.visited:
        #         self.source_station = self.stations[e.station_id]
        #         print(self.source_station)
                




        
        


env = simpy.Environment()
city = City(env, data)
env.run(until=100)