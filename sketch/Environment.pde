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
  stroke(cboost);
  strokeJoin(ROUND);
  noFill();
  int h = 12;
  for (float x=road_x+station_w+h+2; x < width-road_x-station_w-h*2; x = x+h) {
    beginShape();
    vertex(x, road_y-station_h+station_m);
    vertex(x+15, road_y);
    vertex(x, road_y+station_h-station_m);
    endShape();
  }
}

void source_boost(){
  strokeWeight(1);
  stroke(csource);
  strokeJoin(ROUND);
  noFill();
  int h = 12;
  for (float y=road_y+station_h+station_m+h; y < agent_y-agent_R/2-h; y = y+h) {
    beginShape();
    vertex(road_x - h, y);
    vertex(road_x, y-6);
    vertex(road_x + h, y);
    endShape();
  }
}

void target_boost(){
  strokeWeight(1);
  stroke(ctarget);
  strokeJoin(ROUND);
  noFill();
  int h = 12;
  for (float y=road_y+station_h+station_m+h; y < agent_y-agent_R/2-h; y = y+h) {
    beginShape();
    vertex(width-road_x - h, y);
    vertex(width-road_x, y+6);
    vertex(width-road_x + h, y);
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
  for (float r = 0; r < agent_R*2; r+=2) {
    fill(csource, 1);
    circle(road_x, agent_y, noise(r)*r);
    fill(ctarget,1);
    circle(width-road_x, agent_y, noise(r)*r);
  }
  noFill();
  f+=fi;
  if(f > 255 | f<0) fi *= -1;
  stroke(csource, f);
  circle(road_x, agent_y, agent_R);
  stroke(ctarget, f);
  circle(width-road_x, agent_y, agent_R);
}

void environment() {   
  road();
  road_boost();
  source_boost();
  target_boost();
  //station_text();
  agent_source();
}
