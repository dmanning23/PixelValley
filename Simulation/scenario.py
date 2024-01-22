import datetime as dt
import pandas as pd

class Scenario:

    def __init__(self,
                 name,
                 description = None,
                 locations = None,
                 agents = None,
                 _id = None,
                 currentDateTime = None,
                 seed=None,
                 imageFilename = ""):
        if _id is not None:
            self._id = _id
        self.name = name
        self.description = description
        self.locations = locations
        self.agents = agents
        self.seed = seed
        self.imageFilename = imageFilename

        #set the date time!
        if currentDateTime is None:
            currentDateTime = dt.date.today()
        if isinstance(currentDateTime, str):
            #The datetime was passed in as a string
            try:
                currentDateTime = pd.to_datetime(currentDateTime)
            except:
                #There was something wrong with the datetime string
                currentDateTime = dt.date.today()
        elif isinstance(currentDateTime, int):
            #The datetime was passed in as a year. The generator does this
            currentDateTime = dt.datetime(currentDateTime, 1, 1)
        self.currentDateTime = currentDateTime

    def __str__(self) -> str:
        return f"{self.name} in the year {self.currentDateTime.year}. {self.description}"
    
    def GetLocations(self):
        locations = self.locations
        for location in self.locations:
            locations = locations + location.GetLocations()

        return locations
    
    def GetAgents(self):
        agents = []
        if self.agents is not None:
            agents = agents + self.agents
        for location in self.locations:
            agents = agents + location.GetAgents()

        return agents

    def FindAgent(self, agent):
        if self.agents is not None:
            if agent in self.agents:
                #Return None and sort this out later
                return None
        for location in self.locations:
            result = location.FindAgent(agent)
            if result is not None:
                return result
            
    def FindLocation(self, locationName):
        #Check if the location we are trying to get is the great outdoors
        if locationName.lower() == "outside":
            return None
        
        #Go through the list of locations and try to find that location
        for location in self.locations:
            result = location.FindLocation(locationName)
            if result is not None:
                return result
            
        #The location was not found
        return None
    
