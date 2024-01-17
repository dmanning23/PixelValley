from Simulation.finiteStateMachine import *
from mongoengine import *
from py_linq import *
from Models.agentModel import AgentModel

class Dialogue(EmbeddedDocument):
    agentName = StringField()
    text = StringField()

    def __str__(self):
        return f"{self.agentName}: {self.text}"

class Conversation(Document):

    agents = ListField(ReferenceField('AgentModel'))
    summary = StringField()
    dialogue = ListField(EmbeddedDocumentField(Dialogue))
