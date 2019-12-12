
class Agent{
  
  PVector p0, p1, p2, p3, p4, p;
  int agent_id, bus_id;
  float ts_source, ts_bus_available, ts_bus_departed, ts_bus_joined, ts_destination, ts_simulation;
  Bus bus;
  
  float k, ts_extra = 3;
  
  Agent(TableRow row, ArrayList<Bus> buses){
    agent_id = row.getInt("agent_id");
    bus_id = row.getInt("bus_id");
    ts_source = row.getFloat("ts_source");
    ts_bus_available = row.getFloat("ts_bus_available");
    ts_bus_departed = row.getFloat("ts_bus_departed");
    ts_bus_joined = row.getFloat("ts_bus_joined");
    ts_destination = row.getFloat("ts_destination");
    ts_simulation = row.getFloat("ts_simulation");
    
    bus = buses.get(bus_id);
    
    init();
  }
  
  void init() {
    p0 = new PVector(50, height/2 - 150);
    p1 = new PVector(50, height/2 - 50);
    p2 = new PVector(50, height/2 + bus_id*20);
    p3 = new PVector(550, height/2 - 100);
  }
  
  void update(float ts, ArrayList<Agent> agents){
    if (ts > ts_destination & ts < ts_destination + ts_extra) {
      k = (ts-ts_destination)/ts_extra;
      p = PVector.lerp(bus.p2.copy(), p3, k);
    } else if (ts > ts_bus_departed & ts < ts_destination) {
      k = (ts-ts_bus_departed)/(ts_destination-ts_bus_departed);
      p = bus.p.copy();
    } else if (ts > ts_bus_available & ts < ts_bus_joined) {
      k = (ts-ts_bus_available)/(ts_bus_joined-ts_bus_available);
      p = PVector.lerp(p0, p1, k);
    } else if (ts > ts_source-ts_extra & ts < ts_source) {
      k = (ts-ts_source + ts_extra)/ts_extra;
      p = PVector.lerp(p0, p1, k);
    }
  }
  
  boolean checkCollision(ArrayList<Agent> agents){
   return false; 
  }

  void display(float ts) {
    if (ts > ts_source && ts < ts_destination + ts_extra) {
      fill(255,0,0);
      noStroke();
      circle(p.x, p.y, 10);
    }
  }
}
