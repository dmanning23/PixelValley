from Simulation.agent import Agent
from Models.itemModel import ItemSubModel
from mongoengine import *

class AgentLocationModel(Document):
    agentId = ObjectIdField()
    homeScenarioId = ObjectIdField()
    currentScenarioId = ObjectIdField()
    locationId = ObjectIdField()

    def Set(self,
            agentId,
            homeScenarioId,
            currentScenarioId=None,
            locationId=None):
        self.agentId = agentId
        self.homeScenarioId = homeScenarioId
        self.locationId = locationId
        if currentScenarioId is None:
            self.currentScenarioId = homeScenarioId
        else:
            self.currentScenarioId = currentScenarioId
