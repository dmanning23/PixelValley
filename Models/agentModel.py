from Simulation.agent import Agent
from Models.itemModel import ItemSubModel
from mongoengine import *

class AgentModel(Document):
    name = StringField()
    age = IntField()
    gender = StringField()
    description = StringField()
    currentTime = IntField()
    status = StringField()
    emoji = StringField()

    currentItem = EmbeddedDocumentField(ItemSubModel)

    #is the agent currently using the held item?
    isUsingHeldItem = BooleanField()

    timeOfLastReflection = IntField(default=0)

    #TODO: move all these filenames into the description or something

    #TODO: these are all moved out
    portraitFilename = StringField()
    iconFilename = StringField()
    resizedIconFilename = StringField()
    chibiFilename = StringField()
    resizedChibiFilename = StringField()
    homeScenarioId = ObjectIdField()
    currentScenarioId = ObjectIdField()
    locationId = ObjectIdField()

    def Set(self, agent):
        if hasattr(agent, "_id"):
            self.id=agent._id
        self.name = agent.name
        self.age = agent.age
        self.gender = agent.gender
        self.description = agent.description
        self.currentTime = agent.currentTime

        self.status = agent.status
        self.emoji = agent.emoji

        if agent.currentItem is not None:
            self.currentItem = ItemSubModel()
            self.currentItem.Set(agent.currentItem)
        else:
            self.currentItem = None

        self.isUsingHeldItem = agent.IsUsingHeldItem()
        self.timeOfLastReflection = agent.timeOfLastReflection

    def Hydrate(self):
        agent = Agent(self.name,
                     self.age,
                     self.gender,
                     self.description,
                     self.id,
                     currentTime=self.currentTime,
                     status = self.status,
                     emoji = self.emoji,
                     timeOfLastReflection=self.timeOfLastReflection,)
        
        if self.currentItem:
            agent.currentItem = self.currentItem.Hydrate()

        if self.isUsingHeldItem:
            agent.usingItem = agent.currentItem

        return agent