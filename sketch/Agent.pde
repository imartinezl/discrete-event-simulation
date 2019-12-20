class Agent { //<>// //<>//

  PVector p0, p1, p2, pos, prev_pos, source;
  boolean has_bus, with_collision = true, new_target = true;
  int agent_id, bus_id;
  float ts_source, ts_bus_available, ts_bus_departed, ts_bus_joined, ts_bus_reached, ts_destination, ts_simulation;
  Bus bus;
  float [] ts_list;
  PVector[] source_list;

  float k, r=agent_r;
  int n = 0;

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
    p0 = new PVector(road_x, agent_y);
    p1 = new PVector(road_x, height-road_y);
    p2 = new PVector(width-road_x, agent_y);
    if (has_bus) {
      ts_list = new float[]{ts_source, ts_bus_available, ts_bus_joined, ts_bus_departed, ts_bus_reached, ts_destination};
      source_list = new PVector[]{p0, p0, bus.p1, bus.p1, bus.p2, p2};
    }
    source = p0;
    pos = source;
  }

  boolean isAlive(float ts) {
    return ts > ts_source;
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
        move(agents, false);
      }
    } else {
      if (ts > ts_source) {
        move(agents, false);
      }
    }
  }

  float theta=0, m=2*r;
  void move(ArrayList<Agent> agents, boolean attract) {
    if (with_collision) {
      prev_pos = pos;
      PVector d = PVector.sub(source, prev_pos);
      pos = PVector.add(prev_pos, PVector.add(d, PVector.fromAngle(theta).mult(m)));
      if (attract) {
        m = m - 1;
        m = max(m, 0);
      }
      while (check_collision(agents)) {
        int n_r = floor(PI/asin(r/(m-r))); // https://math.stackexchange.com/questions/1808871/for-a-ring-of-n-tangent-circles-inscribed-within-the-perimeter-of-a-larger-circl
        n_r = max(n_r, 1);
        theta = theta + TWO_PI/n_r;
        if (theta >= TWO_PI) {
          m = m + 1;
          theta = 0.0;
        }
        pos = PVector.add(prev_pos, PVector.add(d, PVector.fromAngle(theta).mult(m)));
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
    new_target = n_new != n;
    if (with_collision & new_target) {
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
      if (agent_id != agent.agent_id & agent.pos != null & pos != null & agent.n == n & agent.isAlive(ts)) {
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
    if (ts > ts_source) {
      colorMode(HSB);
      fill(csource);
      if (has_bus) {
        if (ts > ts_bus_joined & ts < ts_bus_departed) {
          fill(#f49d0e);
        } else if ( ts > ts_bus_departed & ts < ts_bus_reached ) {
          fill(#ffc300);
        } else if ( ts > ts_bus_reached) {
          fill(ctarget);
        }
      }
      noStroke();
      circle(pos.x, pos.y, r*2);
      //fill(0);
      //textAlign(CENTER, CENTER);
      //text(agent_id, pos.x, pos.y);
    }
  }
}
