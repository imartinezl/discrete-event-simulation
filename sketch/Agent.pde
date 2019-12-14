 //<>//
class Agent {

  PVector p0, p1, p2, pos, prev_pos, source;
  boolean has_bus, with_collision = true;
  int agent_id, bus_id;
  float ts_source, ts_bus_available, ts_bus_departed, ts_bus_joined, ts_bus_reached, ts_destination, ts_simulation;
  Bus bus;
  float [] ts_list;
  PVector[] source_list;

  float k, r=5;
  int n = -1;

  Agent(TableRow row, ArrayList<Bus> buses) {
    agent_id = row.getInt("agent_id");
    has_bus = boolean(row.getString("has_bus"));
    ts_source = row.getFloat("ts_source");
    if (has_bus) {
      bus_id = row.getInt("bus_id");
      ts_bus_available = row.getFloat("ts_bus_available");
      ts_bus_departed = row.getFloat("ts_bus_departed");
      ts_bus_joined = row.getFloat("ts_bus_joined");
      ts_bus_reached = row.getFloat("ts_bus_reached");
      ts_destination = row.getFloat("ts_destination");
      ts_simulation = row.getFloat("ts_simulation");

      bus = buses.get(bus_id);
    }
  }

  void init() {
    p0 = new PVector(100, height/2);
    p1 = new PVector(100, height/2+100);
    p2 = new PVector(500, height/2);
    if (has_bus) {
      ts_list = new float[]{ts_source, ts_bus_available, ts_bus_joined, ts_bus_departed, ts_bus_reached, ts_destination};
      source_list = new PVector[]{p0, p1, bus.p1, bus.p1, bus.p2, p2};
    }
    pos = p0;
    source = p0;
  }

  boolean isDead(float ts) {
    if (has_bus) {
      return ts > ts_destination;
    }
    return false;
  }

  void update(float ts, ArrayList<Agent> agents) {
    if (has_bus) {
      if (ts > ts_source & ts < ts_destination) {
        update_source(ts);
        move(agents);
      }
    } else {
      if (ts > ts_source) {
        move(agents);
      }
    }
  }

  float theta=0, m=2*r;
  void move(ArrayList<Agent> agents) {
    if (with_collision) {
      prev_pos = pos;
      PVector d = PVector.sub(source, prev_pos);
      pos = PVector.add(prev_pos, PVector.add(d, PVector.fromAngle(theta).mult(m)));
      m = m - 1;
      m = max(m, 0);
      while (check_collision(agents)) {
        pos = PVector.add(prev_pos, PVector.add(d, PVector.fromAngle(theta).mult(m)));
        //float n = floor(TWO_PI*m/(2*r));
        float n = PI/asin(r/(m-r));
        n = max(n, 1);
        theta = theta + TWO_PI/n;
        if (theta > TWO_PI) {
          m = m + 1;
          theta = 0.0;
        }
      }
    } else {
      pos = source;
    }
  }

  float get_k(float ts, float t1, float t2) {
    float k = (ts-t1)/(t2-t1);
    return constrain(k, 0, 1);
  }

  PVector get_source(float ts, int n) {
    float k = get_k(ts, ts_list[n], ts_list[n+1]);
    return PVector.lerp(source_list[n], source_list[n+1], k);
  }


  void update_source(float ts) {
    int n_new = binary_search(ts_list, ts);
    if (with_collision & n_new != n) {
      m = 2*r;
      theta = 0;
    }
    n = n_new;
    source = get_source(ts, n);
  }

  int binary_search(float[] array, float el) {
    int m = 0;
    int n = array.length - 1;
    while (m <= n) {
      int k = (n + m) >> 1;
      float cmp = el - array[k];
      if (cmp > 0) {
        m = k + 1;
      } else if (cmp < 0) {
        n = k - 1;
      } else {
        return k; //[k, k + 1];
      }
    }
    return n; //[n, n+1];
  }



  boolean check_collision(ArrayList<Agent> agents) {
    boolean collide = false;
    for (Agent agent : agents) {
      if (agent_id != agent.agent_id & agent.pos != null & pos != null) {
        //println(agent_id, agent.agent_id, pos, agent.pos, PVector.dist(pos, agent.pos));
        if (PVector.dist(pos, agent.pos) < 2*r) {
          collide = true;
          break;
        }
      }
    }
    return collide;
  }

  void display(float ts) {
    //if (ts > ts_source & ts < ts_destination) {
    if (ts > ts_source) {
      colorMode(HSB);
      fill(agent_id, 255, 255, 100);
      strokeWeight(1);
      stroke(0);
      circle(pos.x, pos.y, r*2);
    }
  }
}
