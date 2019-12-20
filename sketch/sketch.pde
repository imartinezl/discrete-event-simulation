
// Bus[] buses;
ArrayList<Bus> buses = new ArrayList<Bus>();
ArrayList<Agent> agents = new ArrayList<Agent>();
PShape s;


void setup() {

  size(600, 600);
  //String[] fontList = PFont.list();
  //printArray(fontList);

  Table tableBus = loadTable("buses.csv", "header");
  Table tableAgent = loadTable("agents.csv", "header");
  s = loadShape("blue bus - 90.svg");



  //int nbuses = table.getRowCount(); 
  //buses = new Bus[nbuses];
  for (TableRow row : tableBus.rows()) {
    buses.add(new Bus(row));
  }
  for (TableRow row : tableAgent.rows()) {
    agents.add(new Agent(row, buses));
  }

  for (Agent agent : agents) {
    agent.init();
  }
}


float ts = 0, h = 0.1;
void draw() {
  background(20);
  environment();
  frameRate(200);
  for (Bus bus : buses) {
    bus.update(ts);
    bus.display(ts);
  }
  for (int i=0; i<agents.size(); i++) {
    agents.get(i).update(ts, agents);
    agents.get(i).display(ts);
    //if(agents.get(i).isDead(ts)){
    //agents.remove(i);
    //}
  }
  ts = ts + h;
  if (ts > 1500) {
    noLoop();
  }
  //saveFrame("figures/frame_######.png");
}



void environment() {   
  stroke(255);
  strokeWeight(1);
  line(0, height-120, width, height-120);
  line(0, height-80, width, height-80);
  textAlign(CENTER, CENTER);
  textSize(20);
  text("A", 100, height-60);
  text("B", 500, height-60);
}
