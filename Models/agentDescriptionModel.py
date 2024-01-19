from Simulation.agent import Agent
from mongoengine import *

class AgentDescriptionModel(Document):

    hair = StringField()
    eyes = StringField()
    clothing = ListField()
    distinguishingFeatures = ListField()
    agentId = ObjectIdField()