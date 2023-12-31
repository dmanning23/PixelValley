
class ConversationStream():

    def __init__(self, conversationGenerator, activityStream, retrieval):
        self.conversationGenerator = conversationGenerator
        self.activityStream = activityStream
        self.retrieval = retrieval

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
                        agentMemories.extend(self.retrieval.RetrieveMemories(conversationAgents[i], f'What is {conversationAgents[i].name}\'s relationship with {conversationAgents[j].name}?'))
                memories.append(agentMemories)

            #create a conversation
            conversation = self.conversationGenerator.CreateConversation(scenario, conversationAgents, plannedActivities, memories)

            #TODO: summarize the conversation for each agent
            #TODO: create memories for each agent
            #TODO: save the conversation