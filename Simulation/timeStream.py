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
        for agent in scenario.GetAgents():

            #TODO: will teh agents current activity change when time is updated?

            #TODO: if the planned activity changes, how effective was the agent at completing the previous activity?

            agent.IncrementTime()
            AgentRepository.Update(agent)
