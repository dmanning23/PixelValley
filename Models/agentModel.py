
from Simulation.agent import Agent
from mongoengine import *

class AgentModel(Document):
    name = StringField()
    age = IntField()
    gender = StringField()
    description = StringField()
    homeScenarioId = ObjectIdField()
    currentScenarioId = ObjectIdField()
    locationId = ObjectIdField()

    def Set(self, agent, homeScenarioId, currentScenarioId=None, locationId=None):
        if hasattr(agent, "_id"):
            self.id=agent._id
        self.name = agent.name
        self.age = agent.age
        self.gender = agent.gender
        self.description = agent.description
        self.homeScenarioId = homeScenarioId
        if currentScenarioId is None:
            self.currentScenarioId = homeScenarioId
        else:
            self.currentScenarioId = currentScenarioId
        self.locationId = locationId

    def Hydrate(self):
        return Agent(self.name,
                     self.age,
                     self.gender,
                     self.description,
                     self.id)