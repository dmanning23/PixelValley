from Models.agentModel import AgentModel
from Simulation.location import Location
from Simulation.agent import Agent
from py_linq import *

class AgentRepository:
    @staticmethod
    def Create(agent, homeScenarioId, currentScenarioId=None, locationId=None):
        model = AgentModel()
        model.Set(agent, homeScenarioId, currentScenarioId, locationId)

        AgentModel.objects.insert(model)
        agent._id = model.id

    @staticmethod
    def CreateOrUpdate(agent, homeScenarioId, currentScenarioId=None, locationId=None):
        if not hasattr(agent, "_id"):
            AgentRepository.Create(agent, homeScenarioId, currentScenarioId, locationId)
        else:
            model = AgentModel()
            model.Set(agent, homeScenarioId, currentScenarioId, locationId)
            model.save()
        
    @staticmethod
    def Get(agentId):
        model = AgentModel.objects.get(id=agentId)
        return model.Hydate()

    @staticmethod
    def GetAgents(homeScenarioId=None, currentScenarioId=None, locationId=None):
        models = []
        if locationId is not None:
            models = AgentModel.objects(locationId=locationId)
        elif currentScenarioId is not None:
            models = AgentModel.objects(currentScenarioId=currentScenarioId)
        elif homeScenarioId is not None:
            models = AgentModel.objects(homeScenarioId=homeScenarioId)

        #convert to enumerable list of models
        modelCollection = Enumerable(models)

        #convert each model to the simulation object
        return modelCollection.select(lambda x: x.Hydrate())
    
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