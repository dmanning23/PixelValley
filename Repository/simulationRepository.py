from Repository.scenarioRepository import ScenarioRepository
from Repository.locationRepository import LocationRepository
from Repository.agentRepository import AgentRepository
from Repository.itemRepository import ItemRepository

class SimulationRepository:

    def SaveScenario(self, userId, scenario):
        ScenarioRepository.CreateOrUpdate(userId, scenario)

    def SaveAgents(self, scenario):
        #write out all the agents
        if scenario.agents is not None:
            for agent in scenario.agents:
                AgentRepository.CreateOrUpdate(agent, homeScenarioId=scenario._id)
        for location in scenario.locations:
            AgentRepository.CreateOrUpdateFromLocation(location, homeScenarioId=scenario._id)

    def SaveItems(self, scenario):
        for location in scenario.locations:
                ItemRepository.CreateOrUpdateFromLocation(location)

    def SaveLocations(self, scenario):
        for location in scenario.locations:
                LocationRepository.CreateOrUpdateLocations(location, scenario._id)
