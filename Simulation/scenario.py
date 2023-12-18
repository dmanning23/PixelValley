import datetime as dt
import pandas as pd

class Scenario:

    def __init__(self, name, description = None, locations = None, agents = None, _id = None, currentDateTime = None):
        if _id is not None:
            self._id = _id
        self.name = name
        self.description = description
        self.locations = locations
        self.agents = agents

        if currentDateTime is None:
            currentDateTime = dt.datetime.now()
        if isinstance(currentDateTime, str):
            currentDateTime = pd.to_datetime(currentDateTime)
        self.currentDateTime = currentDateTime

    def __str__(self) -> str:
        return self.name
    
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
