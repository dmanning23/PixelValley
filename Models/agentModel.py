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
    currentTime = IntField()
    status = StringField()
    emoji = StringField()
    portraitFilename = StringField()

    def Set(self,
            agent,
            homeScenarioId,
            currentScenarioId=None,
            locationId=None):
        if hasattr(agent, "_id"):
            self.id=agent._id
        self.name = agent.name
        self.age = agent.age
        self.gender = agent.gender
        self.description = agent.description
        self.homeScenarioId = homeScenarioId
        self.currentTime = agent.currentTime
        if currentScenarioId is None:
            self.currentScenarioId = homeScenarioId
        else:
            self.currentScenarioId = currentScenarioId
        self.locationId = locationId
        self.usingItemId = agent.usingItem._id
        self.status = agent.status
        self.emoji = agent.emoji
        self.portraitFilename = agent.portraitFilename

    def Hydrate(self):
        return Agent(self.name,
                     self.age,
                     self.gender,
                     self.description,
                     self.id,
                     currentTime=self.currentTime,
                     status = self.status,
                     emoji = self.emoji,
                     portraitFilename = self.portraitFilename)