from mongoengine import *
from Simulation.item import Item
from Models.finiteStateMachineModel import FiniteStateMachineModel

class ItemModel(Document):
    name = StringField()
    description = StringField()
    canInteract = BooleanField()
    canBePickedUp = BooleanField()
    stateMachine = EmbeddedDocumentField(FiniteStateMachineModel)

    #This will be populated if the item is in a location
    locationId = ObjectIdField()

    #This will be populated if the item is being carried by a character
    characterId = ObjectIdField()

    def Set(self, item, locationId=None, characterId=None):
        if hasattr(item, "_id"):
            self.id=item._id
        self.name = item.name
        self.description = item.description
        self.canInteract = item.canInteract
        self.canBePickedUp = item.canBePickedUp
        self.locationId=locationId
        self.characterId = characterId

        #the state machine has to be set up separately
        if item.stateMachine is not None:
            self.stateMachine = FiniteStateMachineModel()
            self.stateMachine.Set(item.stateMachine)

    def Hydrate(self):
        item = Item(self.name,
                    self.description,
                    self.canInteract,
                    self.canBePickedUp,
                    _id = self.id)
        
        if self.stateMachine is not None:
            item.stateMachine = self.stateMachine.Hydrate()

        return item

