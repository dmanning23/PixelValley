from Repository.agentRepository import AgentRepository
from Repository.scenarioRepository import ScenarioRepository
from datetime import timedelta

class TimeStream():

    def __init__(self):
        pass

    def IncrementTime(self, userId, scenario):
        #Add 15 minutes to the scenario
        scenario.currentDateTime = scenario.currentDateTime + timedelta(minutes = 15)
        ScenarioRepository.CreateOrUpdate(userId, scenario)

        #Increment each agents time
        for agent in scenario.agents:
            agent.IncrementTime()
            AgentRepository.Update(agent, homeScenarioId=scenario._id)
            for childLocation in scenario.locations:
                self._incrementLocationTime(userId, scenario, childLocation)

    def _incrementLocationTime(self, userId, scenario, location):
        #increment the time for all the agents in this location
        if location.agents is not None:
            for agent in location.agents:
                agent.IncrementTime()
                AgentRepository.Update(agent, homeScenarioId=scenario._id, locationId=location._id)
        #recurse into all teh child locations
        if location.locations is not None:
            for childLocation in location.locations:
                self._incrementLocationTime(userId, scenario, childLocation)
