
class Agent{
  
  PVector origin, destination;
  int agent_id;
  float ts_source, ts_bus_available, ts_bus_departed, ts_bus_joined, ts_destination, ts_simulation;
  
  Agent(TableRow row){
    agent_id = row.getInt("agent_id");
    ts_source = row.getFloat("ts_source");
    ts_bus_available = row.getFloat("ts_bus_available");
    ts_bus_departed = row.getFloat("ts_bus_departed");
    ts_bus_joined = row.getFloat("ts_bus_joined");
    ts_destination = row.getFloat("ts_destination");
    ts_simulation = row.getFloat("ts_simulation");
  }
  
}
