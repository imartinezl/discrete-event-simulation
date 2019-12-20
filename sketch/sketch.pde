
// Bus[] buses;
ArrayList<Bus> buses = new ArrayList<Bus>();
ArrayList<Agent> agents = new ArrayList<Agent>();
PFont font;
PShape s;
float road_x = 100, road_y = 150, station_h = 35, station_w = 50, station_m = 12, agent_y = 450, agent_r = 3;

void setup() {

  size(800, 600);
  String[] fontList = PFont.list();
  printArray(fontList);

  Table tableBus = loadTable("buses.csv", "header");
  Table tableAgent = loadTable("agents.csv", "header");
  s = loadShape("bus.svg");
  s = loadShape("bus2.svg");

  String fontName = "Lato Medium"; // "Roboto Condensed Bold"
  font = createFont(fontName, 32);


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


float ts = 0, h = 0.5;
void draw() {
  background(50);
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
