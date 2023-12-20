import datetime as dt
import pandas as pd

class Scenario:

    def __init__(self, name, description = None, locations = None, agents = None, _id = None, currentDateTime = None, seed=None):
        if _id is not None:
            self._id = _id
        self.name = name
        self.description = description
        self.locations = locations
        self.agents = agents
        self.seed = seed

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
    
    def GetAgentLocation(self, agent):
        if self.agents is not None:
            if agent in self.agents:
                #Return None and sort this out later
                return None
        for location in self.locations:
            result = location.GetAgentLocation(agent)
            if result is not None:
                return result
