from Models.itemModel import ItemModel
from py_linq import *

class ItemRepository:
    @staticmethod
    def Create(item, locationId=None, characterId=None):
        model = ItemModel()
        model.Set(item, locationId, characterId)

        ItemModel.objects.insert(model)
        item._id = model.id

    @staticmethod
    def CreateOrUpdate(item, locationId=None, characterId=None):
        if not hasattr(item, "_id"):
            ItemRepository.Create(item, locationId, characterId)
        else:
            ItemRepository.Update(item, locationId, characterId)

    @staticmethod
    def Update(item, locationId=None, characterId=None):
        model = ItemModel()
        model.Set(item, locationId, characterId)
        model.save()
        
    @staticmethod
    def Get(itemId):
        model = ItemModel.objects.get(id=itemId)
        return model.Hydate()

    @staticmethod
    def GetItems(locationId=None, characterId=None):
        models = []
        if locationId is not None:
            models = ItemModel.objects(locationId=locationId)
        elif characterId is not None:
            models = ItemModel.objects(characterId=characterId)

        #convert to enumerable list of models
        modelCollection = Enumerable(models)

        #convert each model to the simulation object
        return modelCollection.select(lambda x: x.Hydrate()).to_list()
    
    @staticmethod
    def FetchLocation(location):
        location.items = ItemRepository.GetItems(locationId=location._id)
        if location.locations is not None:
            for childLocation in location.locations:
                ItemRepository.FetchLocation(childLocation)

    @staticmethod
    def CreateOrUpdateFromLocation(location):
        if location.items is not None:
            for item in location.items:
                ItemRepository.CreateOrUpdate(item, locationId=location._id)

        #write out child items
        if location.locations is not None:
            for childLocation in location.locations:
                ItemRepository.CreateOrUpdateFromLocation(childLocation)

    def GetItemByName(self, name):
        model = ItemModel.objects.get(name=name)
        if model is not None:
            return model.Hydate()
        return None