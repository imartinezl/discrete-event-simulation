
class Bus {

  PVector p0, p1, p2, p3, pos;
  int bus_id;
  boolean bus_is_full, driver_out_patience;
  float ts_source, ts_departed, ts_reached, ts_destination;
  float k, ts_extra = 10;

  Bus(TableRow row) {
    bus_id = row.getInt("bus_id");
    bus_is_full = boolean(row.getString("bus_is_full"));
    driver_out_patience = boolean(row.getString("driver_out_patience"));
    ts_source = row.getFloat("ts_source");
    ts_departed = row.getFloat("ts_departed");
    ts_reached = row.getFloat("ts_reached");
    ts_destination = row.getFloat("ts_destination");

    init();
  }

  void init() {
    //float s = randomGaussian()*10;
    p0 = new PVector(-road_x, road_y);
    p1 = new PVector(road_x, road_y);
    p2 = new PVector(width-road_x, road_y);
    p3 = new PVector(width+road_x, road_y);
  }

  void update(float ts) {
    if (ts > ts_destination-h & ts < ts_destination + ts_extra + h) {
      k = (ts-ts_destination)/ts_extra;
      pos = PVector.lerp(p2, p3, k);
    } else if (ts > ts_departed-h & ts < ts_reached + h) {
      k = (ts-ts_departed)/(ts_reached-ts_departed);
      pos = PVector.lerp(p1, p2, k);
    } else if (ts > ts_source-ts_extra-h & ts < ts_source + h) {
      k = (ts-(ts_source - ts_extra))/ts_extra;
      pos = PVector.lerp(p0, p1, k);
    }
  }

  void bus_svg() {
    pushMatrix();
    translate(pos.x, pos.y);
    rotate(PI/2);
    shapeMode(CENTER);
    shape(s, 0, 0, 40, 80);
    popMatrix();
  }

  void bus_rect() {
    colorMode(RGB);
    noStroke();
    fill(#f40eea);
    rectMode(CENTER);
    rect(pos.x, pos.y, 70, 30);
  }

  void display(float ts) {
    if (ts > ts_source - ts_extra & ts < ts_destination + ts_extra) {
      //bus_rect();
      bus_svg();
    }
  }
}
