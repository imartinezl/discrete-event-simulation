
class Bus {

  PVector origin, destination, current;
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
  }

  void init() {
    origin = PVector.random2D();
    destination = PVector.random2D();
  }
  
  void update(float ts){
    float k = (ts-ts_departed)/(ts_destination-ts_departed);
    k = constrain(k, 0, 1);
    current = PVector.lerp(origin, destination, k);
  }

  void display(float ts) {
    if (ts > ts_source) {
      noFill();
      stroke(0);
      circle(current.x, current.y, 10);
    }
  }
}
