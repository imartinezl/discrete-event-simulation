void road() {
  stroke(255);
  strokeWeight(2.5);
  line(0, road_y-station_h, width, road_y-station_h);
  line(0, road_y+station_h, width, road_y+station_h);
  strokeWeight(1.5);
  line(road_x-station_w, road_y+station_h-station_m, road_x-station_w, road_y-station_h+station_m);
  line(road_x+station_w, road_y+station_h-station_m, road_x+station_w, road_y-station_h+station_m);
  line(width-road_x-station_w, road_y+station_h-station_m, width-road_x-station_w, road_y-station_h+station_m);
  line(width-road_x+station_w, road_y+station_h-station_m, width-road_x+station_w, road_y-station_h+station_m);
}

void road_boost() {
  strokeWeight(1.5);
  stroke(#fffb11);
  strokeJoin(ROUND);
  noFill();
  int h = 12;
  for (float x=road_x+station_w+h; x < width-road_x-station_w-h; x = x+h) {
    beginShape();
    vertex(x, road_y-station_h+station_m);
    vertex(x+15, road_y);
    vertex(x, road_y+station_h-station_m);
    endShape();
  }
}

void station_text() {
  textAlign(CENTER, CENTER);
  textFont(font);
  textSize(20);
  fill(255);
  text("A", road_x, road_y-2*station_h);
  text("B", width-road_x, road_y-2*station_h);
}

float f = 0, fi=5;
void agent_source() {
  noStroke();
  for (float r = 0; r < 200; r+=2) {
    fill(255, 1);
    circle(road_x, agent_y, noise(r)*r);
    circle(width-road_x, agent_y, noise(r)*r);
  }
  noFill();
  f+=fi;
  if(f > 255 | f<0) fi *= -1;
  stroke(#ff4711, f);
  circle(road_x, agent_y, 100);
  stroke(#1147ff, f);
  circle(width-road_x, agent_y, 100);
}

void environment() {   
  road();
  road_boost();
  //station_text();
  agent_source();
}
