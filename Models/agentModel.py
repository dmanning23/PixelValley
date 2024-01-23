from Simulation.agent import Agent
from Models.itemModel import ItemSubModel
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

    currentItem = EmbeddedDocumentField(ItemSubModel)

    #is the agent currently using the held item?
    isUsingHeldItem = BooleanField()

    #TODO: move all these filenames into the description or something
    portraitFilename = StringField()
    iconFilename = StringField()
    resizedIconFilename = StringField()
    chibiFilename = StringField()
    resizedChibiFilename = StringField()

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

        self.status = agent.status
        self.emoji = agent.emoji

        if agent.currentItem is not None:
            self.currentItem = ItemSubModel()
            self.currentItem.Set(agent.currentItem)
        else:
            self.currentItem = None

        self.isUsingHeldItem = ((agent.currentItem is not None) and (agent.usingItem is not None) and (agent.currentItem.name == agent.usingItem.name))

        self.portraitFilename = agent.portraitFilename
        self.iconFilename = agent.iconFilename
        self.resizedIconFilename = agent.resizedIconFilename
        self.chibiFilename = agent.chibiFilename
        self.resizedChibiFilename = agent.resizedChibiFilename

    def Hydrate(self):
        agent = Agent(self.name,
                     self.age,
                     self.gender,
                     self.description,
                     self.id,
                     currentTime=self.currentTime,
                     status = self.status,
                     emoji = self.emoji,
                     portraitFilename = self.portraitFilename,
                     iconFilename = self.iconFilename,
                     resizedIconFilename = self.resizedIconFilename,
                     chibiFilename = self.chibiFilename,
                     resizedChibiFilename = self.resizedChibiFilename,)
        
        if self.currentItem:
            agent.currentItem = self.currentItem.Hydrate()

        if self.isUsingHeldItem:
            agent.usingItem = agent.currentItem

        return agent