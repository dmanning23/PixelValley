from py_linq import *
from ConversationEngine.conversationModel import ConversationModel

class ConversationStream():

    def __init__(self, conversationGenerator, activityStream, retrieval, memoryRepository, conversationSummarizer, conversationStarter):
        self.conversationGenerator = conversationGenerator
        self.activityStream = activityStream
        self.retrieval = retrieval
        self.memoryRepository = memoryRepository
        self.conversationSummarizer = conversationSummarizer
        self.conversationStarter = conversationStarter

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
            locationAgentMemories = self.retrieval.RetrieveMemories(agent, f'What is my relationship with {locationAgent.name}?', 4)
            memories.append(locationAgentMemories)

        #Choose whether or not to start a conversation
        agents, reasoning = self.conversationStarter.StartConversation(scenario, agent, plannedActivity, locationAgents, memories)

        if agents is not None:
            #create memory that Agent decided to talk to Agent1, Agent2, etc.
            self.memoryRepository.CreateMemory(agent, reasoning)

            #create the conversation
            conversationModel = ConversationModel(initiatingAgent = agent._id, reasoning = reasoning)
            conversationModel.agents = Enumerable(agents).select(lambda x: x._id).to_list()
            ConversationModel.objects.insert(conversationModel)

            return conversationModel, agents
        #This agent chose not to start a conversation
        return None, None

    def CreateConversation(self, scenario, conversationModel, agents):
            #get the planned activity of each agent
            plannedActivities = []
            for agent in agents:
                plannedActivities.append(self.activityStream.GetCurrentPlannedActivity(agent, scenario.currentDateTime))

            #get memories for each agent
            memories = []
            for i in range(len(agents)):
                agentMemories = []
                for j in range(len(agents)):
                    if i != j:
                        agentMemories.extend(self.retrieval.RetrieveMemories(agents[i], f'What is my relationship with {agents[j].name}?', 5))
                memories.append(agentMemories)

            #create a conversation
            conversationModel = self.conversationGenerator.CreateConversation(scenario, conversationModel, agents, plannedActivities, memories)

            if conversationModel is not None:
                #summarize the conversation for each agent
                for agent in agents:
                    #create memories for each agent
                    self.memoryRepository.CreateMemory(agent, f"I had a conversation at {scenario.currentDateTime}: {conversationModel.summary}")
                    summaries = self.conversationSummarizer.SummarizeConversation(agent, conversationModel)
                    if summaries is not None:
                        for summary in summaries:
                            self.memoryRepository.CreateMemory(agent, f"{summary}")
                #save the conversation
                conversationModel.save()

    def ConversationPipeline(self, scenario, agent):
        conversationModel, chosenAgents = self.conversationStream.StartConversation(scenario, agent)
        if chosenAgents is not None and len(chosenAgents) > 1:
            return self.conversationStream.CreateConversation(scenario, conversationModel, chosenAgents)
