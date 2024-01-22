from Simulation.finiteStateMachine import *
from mongoengine import *
from py_linq import *
from Models.agentModel import AgentModel

class DialogueModel(EmbeddedDocument):
    agentName = StringField()
    text = StringField()

    def __str__(self):
        return f"{self.agentName}: {self.text}"

class ConversationModel(Document):

    #The person who initiated the conversation
    initiatingAgent = ObjectIdField()

    #Why that person chose to initiate the conversation
    reasoning = StringField()

    agents = ListField(ReferenceField('AgentModel'))
    summary = StringField()
    dialogue = ListField(EmbeddedDocumentField(DialogueModel))
