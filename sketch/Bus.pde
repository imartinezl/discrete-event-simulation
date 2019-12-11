
class Bus {

  PVector origin, destination, path, current;
  int bus_id;
  boolean bus_is_full, driver_out_patience;
  float ts_source, ts_departed;

  Bus(TableRow row) {
    bus_id = row.getInt("bus_id");
    bus_is_full = boolean(row.getString("bus_is_full"));
    driver_out_patience = boolean(row.getString("driver_out_patience"));
    ts_source = row.getFloat("ts_source");
    ts_departed = row.getFloat("ts_departed");
  }

  void init() {
    origin = PVector.random2D();
    destination = PVector.random2D();
    path = destination.sub(origin);
  }
  
  void update(float t){
    current =   
  }

  void display(float t) {
    if (t > ts_source) {
      noFill();
      stroke(0);
      circle(current.x, current.y, 10);
    }
  }
}
