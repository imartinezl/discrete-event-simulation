
// Bus[] buses;
ArrayList<Bus> buses = new ArrayList<Bus>();
ArrayList<Agent> agents = new ArrayList<Agent>();

void setup() {

  size(600,600);
  
  Table tableBus = loadTable("buses.csv", "header");
  Table tableAgent = loadTable("agents.csv", "header");
  //int nbuses = table.getRowCount(); 
  //buses = new Bus[nbuses];
  for (TableRow row : tableBus.rows()) {
    buses.add(new Bus(row));
  }
  for (TableRow row : tableAgent.rows()) {
    agents.add(new Agent(row, buses));
  }

  for(Agent agent: agents){
    agent.init();
  }
}


float ts = 0.0, h = 0.05;
void draw(){
  background(255);
  frameRate(200);
  for(Bus bus: buses){
    bus.update(ts);
    bus.display(ts);
  }
  for(int i=0; i<agents.size(); i++){
    agents.get(i).update(ts, agents);
    agents.get(i).display(ts);
    if(agents.get(i).isDead(ts)){
      //agents.remove(i);
    }
  }
  ts = ts + h;
  if(abs(ts % 1) < h){
    //println(ts);
  }
  if(ts > 1500){
    noLoop();
  }
}
