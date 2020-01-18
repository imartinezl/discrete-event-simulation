# %%

import pandas as pd
import matplotlib.pyplot as plt

buses = pd.read_csv('buses.csv')
agents = pd.read_csv('agents.csv')


# %% BUSES
buses['ts_waiting'] = buses.ts_departed - buses.ts_source
buses['ts_travel'] = buses.ts_reached - buses.ts_departed
buses['ts_total'] = buses.ts_destination - buses.ts_source

fig, ax = plt.subplots(2, 2, figsize=(12,6))
ax[0][0].hist(buses.bus_is_full.astype(int), bins=2)
ax[0][1].hist(buses.driver_out_patience.astype(int), bins=2)
ax[1][0].plot(buses.ts_source, buses.bus_is_full)
ax[1][1].plot(buses.ts_source, buses.driver_out_patience)

fig, ax = plt.subplots(1, 3, figsize=(12,6))
ax[0].hist(buses.ts_waiting, bins=50)
ax[1].hist(buses.ts_travel, bins=10)
ax[2].hist(buses.ts_total, bins=50)


# %% AGENTS
agents['ts_expected'] = agents.ts_target - agents.ts_source


fig, ax = plt.subplots(2, 3, figsize=(12,6), sharex=True)
plt.suptitle('Agents Stats')
ax[0][0].set_title("ts_target")
ax[0][0].hist(agents.ts_source, bins=100, alpha=0.5, label="ts_source")
ax[0][0].hist(agents.ts_target, bins=100, alpha=0.5, label="ts_target")
ax[0][0].legend()
ax[0][1].set_title("ts_destination")
ax[0][1].hist(agents.ts_source, bins=100, alpha=0.5, label="ts_source")
ax[0][1].hist(agents.ts_destination, bins=100, alpha=0.5, label="ts_destination")
ax[0][1].legend()
ax[0][2].set_title("ts_expected vs ts_simulation")
ax[0][2].hist(agents.ts_expected, bins=100, alpha=0.5, label="ts_expected")
ax[0][2].hist(agents.ts_simulation, bins=100, alpha=0.5, label="ts_simulation")
ax[0][2].legend()


# %%
