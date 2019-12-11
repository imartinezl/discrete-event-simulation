
class Bus {

  PVector p0, p1, p;
  int bus_id;
  boolean bus_is_full, driver_out_patience;
  float ts_source, ts_departed, ts_destination;

  Bus(TableRow row) {
    bus_id = row.getInt("bus_id");
    bus_is_full = boolean(row.getString("bus_is_full"));
    driver_out_patience = boolean(row.getString("driver_out_patience"));
    ts_source = row.getFloat("ts_source");
    ts_departed = row.getFloat("ts_departed");
    ts_destination = row.getFloat("ts_destination");

    init();
  }

  void init() {
    float s = randomGaussian()*10;
    p0 = new PVector(50, height/2 + bus_id*20);
    p1 = new PVector(550, height/2 + bus_id*20);
  }

  void update(float ts) {
    float k = (ts-ts_departed)/(ts_destination-ts_departed);
    k = constrain(k, 0, 1);
    p = PVector.lerp(p0, p1, k);
  }

  void display(float ts) {
    if (ts > ts_source) {
      noFill();
      stroke(0);
      if ( ts > ts_departed ) {
        if (bus_is_full) {
          stroke(255, 0, 0);
        } else if (driver_out_patience) {
          stroke(0, 0, 255);
        }
      }
      circle(p.x, p.y, 10);
      rectMode(CENTER);
      rect(p.x, p.y, 40, 20);
    }
  }
}
