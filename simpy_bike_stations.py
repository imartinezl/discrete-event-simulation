
# %%
import simpy
import random

RANDOM_SEED = 42
random.seed(RANDOM_SEED)


data = {
    'stations': [
        {
            'location': [0,0],
            'capacity': 5
        },
        {
            'location': [10,10],
            'capacity': 5
        }
    ],
    'agents': [
        { 
            'age': 18
        },
        { 
            'age': 28
        }
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
            station = Station(self.env, station_id, location, capacity)
            self.stations.append(station)

    def init_agents(self):
        for agent_id in range(self.n_agents):
            agent = Agent(self.env, agent_id)
            self.agents.append(agent)

class Station:

    def __init__(self, env, station_id, location, capacity):
        self.env = env
        self.station_id = station_id
        self.location = location
        self.capacity = capacity

        self.station_res = simpy.Resource(self.env, capacity=self.capacity)
        self.station_con = simpy.Container(self.env, self.capacity, init=self.capacity)

    def empty(self):
        return self.station_con.level == 0

class Agent:

    def __init__(self, env, agent_id):
        self.env = env
        self.agent_id = agent_id

        self.print = True
        self.env.process(self.process())

    def process(self):
        yield self.env.timeout(10)
        if self.print:
            print('Agent %d working at %.2f' % (self.agent_id, self.env.now))

    


env = simpy.Environment()
city = City(env, data)
env.run(until=100)