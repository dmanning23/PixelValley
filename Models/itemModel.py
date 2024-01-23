from mongoengine import *
from Simulation.item import Item
from Models.finiteStateMachineModel import FiniteStateMachineModel

class BaseItemModel():
    name = StringField()
    description = StringField()
    canInteract = BooleanField()
    canBePickedUp = BooleanField()
    stateMachine = EmbeddedDocumentField(FiniteStateMachineModel)

    #This will be populated if the item is in a location
    locationId = ObjectIdField()

    #This will be populated if an item is being used by the character
    usingCharacterId = ObjectIdField()

    status = StringField()
    emoji = StringField()

    def Set(self,
            item,
            locationId=None,
            usingCharacterId=None):
        if hasattr(item, "_id"):
            self.id=item._id
        self.name = item.name
        self.description = item.description
        self.canInteract = item.canInteract
        self.canBePickedUp = item.canBePickedUp
        self.locationId=locationId
        self.usingCharacterId = usingCharacterId
        self.status = item.status
        self.emoji = item.emoji

        #the state machine has to be set up separately
        if item.stateMachine is not None:
            self.stateMachine = FiniteStateMachineModel()
            self.stateMachine.Set(item.stateMachine)

    def Hydrate(self):
        id = None
        if hasattr(self, "id"):
            id=self.id
        item = Item(self.name,
                    self.description,
                    self.canInteract,
                    self.canBePickedUp,
                    _id = id,
                    status = self.status,
                    emoji = self.emoji)
        
        if self.stateMachine is not None:
            item.stateMachine = self.stateMachine.Hydrate()

        return item
    
class ItemModel(BaseItemModel, Document):
    pass

class ItemSubModel(BaseItemModel, EmbeddedDocument):
    pass
