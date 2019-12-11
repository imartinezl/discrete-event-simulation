
// Bus[] buses;
ArrayList<Bus> buses = new ArrayList<Bus>();
ArrayList<Agent> agents = new ArrayList<Agent>();

void setup() {

  Table tableBus = loadTable("buses.csv", "header");
  Table tableAgent = loadTable("agents.csv", "header");
  //int nbuses = table.getRowCount(); 
  //buses = new Bus[nbuses];
  for (TableRow row : tableBus.rows()) {
    buses.add(new Bus(row));
  }
  for (TableRow row : tableAgent.rows()) {
    agents.add(new Agent(row));
  }
  println(buses.get(0).ts_departed);
  println(agents.get(0).ts_source);
}


float ts = 0.0;
void draw(){
  
  ts = ts + 0.01;
}
