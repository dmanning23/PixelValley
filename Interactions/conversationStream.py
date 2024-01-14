from py_linq import *
class ConversationStream():

    def __init__(self, conversationGenerator, activityStream, retrieval):
        self.conversationGenerator = conversationGenerator
        self.activityStream = activityStream
        self.retrieval = retrieval

    def StartConversation(self, scenario, agent):
        location = scenario.FindAgent(agent)

        #Get a list of agents in that location that are NOT the agent
        locationAgents = Enumerable(location.agents)
        locationAgents = locationAgents.where(lambda x: x._id != agent._id).to_list()

        #Get the planned activity of the agent
        plannedActivity = self.activityStream.GetCurrentPlannedActivity(agent, scenario.currentDateTime)

        #get memories for each agent
        memories = []
        for locationAgent in locationAgents:
            memories.append(self.retrieval.RetrieveMemories(agent, f'What is {agent.name}\'s relationship with {locationAgent.name}?', 5))

        #Choose whether or not to start a conversation
        result = self.conversationGenerator.StartConversation(scenario, agent, plannedActivity, locationAgents, memories)

        #TODO: create memory that Agent decided to talk to Agent1, Agent2, etc.

        return result

    def CreateConversation(self, scenario, conversationAgents):
            #get the planned activity of each agent
            plannedActivities = []
            for agent in conversationAgents:
                plannedActivities.append(self.activityStream.GetCurrentPlannedActivity(agent, scenario.currentDateTime))

            #get memories for each agent
            memories = []
            for i in range(len(conversationAgents)):
                agentMemories = []
                for j in range(len(conversationAgents)):
                    if i != j:
                        agentMemories.extend(self.retrieval.RetrieveMemories(conversationAgents[i], f'What is {conversationAgents[i].name}\'s relationship with {conversationAgents[j].name}?', 5))
                memories.append(agentMemories)

            #create a conversation
            conversation = self.conversationGenerator.CreateConversation(scenario, conversationAgents, plannedActivities, memories)

            #TODO: summarize the conversation for each agent
            #TODO: create memories for each agent
            #TODO: save the conversation