from Models.agentModel import AgentModel
from Models.agentLocationModel import AgentLocationModel
from py_linq import *

class AgentRepository:
    @staticmethod
    def Create(agent, homeScenarioId, currentScenarioId=None, locationId=None):
        model = AgentModel()
        model.Set(agent)

        AgentModel.objects.insert(model)
        agent._id = model.id
        AgentRepository.UpdateLocation(agent, homeScenarioId, currentScenarioId, locationId)

    @staticmethod
    def CreateOrUpdate(agent, homeScenarioId, currentScenarioId=None, locationId=None):
        if not hasattr(agent, "_id"):
            AgentRepository.Create(agent, homeScenarioId, currentScenarioId, locationId)
        else:
            AgentRepository.Update(agent)
            AgentRepository.UpdateLocation(agent, homeScenarioId, currentScenarioId, locationId)

    @staticmethod
    def Update(agent):
        model = AgentModel()
        model.Set(agent)
        model.save()
        if agent.currentItem is None:
            AgentModel.objects(id=model.id).update(unset__currentItem=1)

    @staticmethod
    def UpdateLocation(agent, homeScenarioId, currentScenarioId=None, locationId=None):
        #get the agentlocation model for this agent
        model = AgentLocationModel.objects(agentId=agent._id).first()
        
        #create the model if one does not exist
        if model is None:
            model = AgentLocationModel()
            model.Set(agentId=agent._id,
                      homeScenarioId=homeScenarioId,
                      currentScenarioId=currentScenarioId,
                      locationId=locationId)
            AgentLocationModel.objects.insert(model)
        else:
            #update the parameters
            model.Set(agent._id, homeScenarioId, currentScenarioId, locationId)
            #save the updated model
            model.save()
            if locationId is None:
                AgentLocationModel.objects(id=model.id).update(unset__locationId=1)
    
    @staticmethod
    def Get(agentId):
        model = AgentModel.objects.get(id=agentId)
        return model.Hydate()
    
    @staticmethod
    def GetAgents(homeScenarioId=None, currentScenarioId=None, locationId=None):
        if locationId is not None:
            #get the agents in a specific location
            locationModels = AgentLocationModel.objects(locationId=locationId)
        elif currentScenarioId is not None:
            #get ALL the agents that are currently in a specific scenario
            locationModels = AgentLocationModel.objects(currentScenarioId=currentScenarioId)
        elif homeScenarioId is not None:
            #get ALL the agents that originated from a specific scenario
            locationModels = AgentLocationModel.objects(homeScenarioId=homeScenarioId)

        #get the model for each location model
        models = []
        for locationModel in locationModels:
            model = AgentModel.objects(id=locationModel.agentId).first()
            if model is None:
                #TODO: an agent is missing
                pass
            models.append(model)
        #convert to enumerable list of models
        modelCollection = Enumerable(models)

        #convert each model to the simulation object
        return modelCollection.select(lambda x: x.Hydrate()).to_list()
    
    #Get the agents that are standing outside
    @staticmethod
    def GetOutsideAgents(currentScenarioId):
        locationModels = AgentLocationModel.objects(currentScenarioId=currentScenarioId, locationId=None)
        
        #get the model for each location model
        models = []
        for locationModel in locationModels:
            model = AgentModel.objects(id=locationModel.agentId).first()
            if model is None:
                #TODO: an agent is missing
                pass
            models.append(model)

        modelCollection = Enumerable(models)
        return modelCollection.select(lambda x: x.Hydrate()).to_list()

    @staticmethod
    def FetchLocation(location):
        location.agents = AgentRepository.GetAgents(locationId=location._id)
        if location.locations is not None:
            for childLocation in location.locations:
                AgentRepository.FetchLocation(childLocation)

    @staticmethod
    def CreateOrUpdateFromLocation(location, homeScenarioId, currentScenarioId=None):
        if location.agents is not None:
            for agent in location.agents:
                AgentRepository.CreateOrUpdate(agent, homeScenarioId, currentScenarioId, locationId=location._id)

        #write out child items
        if location.locations is not None:
            for childLocation in location.locations:
                AgentRepository.CreateOrUpdateFromLocation(childLocation, homeScenarioId, currentScenarioId)