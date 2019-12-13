
class Agent {

  PVector p0, p1, p2, p;
  boolean has_bus, fixed;
  int agent_id, bus_id;
  float ts_source, ts_bus_available, ts_bus_departed, ts_bus_joined, ts_bus_reached, ts_destination, ts_simulation;
  Bus bus;

  float k, r=5;

  Agent(TableRow row, ArrayList<Bus> buses) {
    agent_id = row.getInt("agent_id");
    has_bus = boolean(row.getString("has_bus"));
    if (has_bus) {
      bus_id = row.getInt("bus_id");
      ts_source = row.getFloat("ts_source");
      ts_bus_available = row.getFloat("ts_bus_available");
      ts_bus_departed = row.getFloat("ts_bus_departed");
      ts_bus_joined = row.getFloat("ts_bus_joined");
      ts_bus_reached = row.getFloat("ts_bus_reached");
      ts_destination = row.getFloat("ts_destination");
      ts_simulation = row.getFloat("ts_simulation");

      bus = buses.get(bus_id);
    }

    init();
  }

  void init() {
    p0 = new PVector(50, height/2 - 50);
    p1 = new PVector(50, height/2 - 20);
    p2 = new PVector(550, height/2 - 20);
    
   
    while (checkCollision(agents)) {
      p0 = p0.add(PVector.random2D());
    }
  }

  //void update(float ts, ArrayList<Agent> agents){
  void update(float ts, ArrayList<Agent> agents) {
    if (has_bus) {
      move(ts);
    } else {
      //if (ts > ts_source - h) {
      //  if (!fixed) {
          p = p0.copy();
      //    while (checkCollision(agents)) {
      //      p = p.add(PVector.random2D());
      //    }
      //    fixed = true;
      //  }
      //}
    }
  }

  void move(float ts) {
    if (ts > ts_bus_reached - h & ts < ts_destination + h) {
      k = (ts-ts_bus_reached)/(ts_destination-ts_bus_reached);
      p = PVector.lerp(bus.p2.copy(), p2, k);
    } else if (ts > ts_bus_departed - h & ts < ts_bus_reached + h) {
      p = bus.p.copy();
    } else if (ts > ts_bus_available - h & ts < ts_bus_joined + h) {
      k = (ts-ts_bus_available)/(ts_bus_joined-ts_bus_available);
      k = constrain(k, 0, 1);
      p = PVector.lerp(p1, bus.p1.copy(), k);
    } else if (ts > ts_source - h & ts < ts_bus_available + h) {
      k = (ts-ts_source)/(ts_bus_available-ts_source);
      p = PVector.lerp(p0, p1, k);
    }
  }

  boolean checkCollision(ArrayList<Agent> agents) {
    boolean collide = false;
    for (Agent agent : agents) {
      if (this.agent_id != agent.agent_id & agent.p != null) {
        //if (pow(this.p.x-agent.p.x, 2) + pow(this.p.y-agent.p.y, 2) <= pow(r, 2)) {
        if (this.p.dist(agent.p) < 2*r) {
          collide = true;
          break;
        }
      }
    }
    return collide;
  }

  void display(float ts) {
    //if (ts > ts_source && ts < ts_destination) {
    if (ts > ts_source) {
      fill(255, 0, 0);
      strokeWeight(1);
      stroke(0);
      circle(p.x, p.y, r*2);
    }
  }
}
