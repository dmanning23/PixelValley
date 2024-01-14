from Simulation.finiteStateMachine import *
from mongoengine import *
from py_linq import *
from Models.agentModel import AgentModel

class Dialogue(EmbeddedDocument):
    agentName = StringField()
    text = StringField()

class Conversation(Document):

    agents = ListField(ReferenceField('AgentModel'))
    summary = StringField()
    dialogue = ListField(EmbeddedDocumentField(Dialogue))
