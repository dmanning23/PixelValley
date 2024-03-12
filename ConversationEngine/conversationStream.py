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

    async def StartConversation(self, scenario, agent):
        location = scenario.FindAgent(agent)

        #Get a list of agents in that location that are NOT the agent
        if location is not None:
            locationAgents = Enumerable(location.agents)
        elif scenario.agents is not None:
            locationAgents = scenario.agents
        else:
            locationAgents = []
        locationAgents = Enumerable(locationAgents).where(lambda x: x._id != agent._id).to_list()

        #Get the planned activity of the agent
        plannedActivity = self.activityStream.GetCurrentPlannedActivity(agent, scenario.currentDateTime)

        #get memories for each agent
        memories = []
        for locationAgent in locationAgents:
            locationAgentMemories = await self.retrieval.RetrieveMemories(agent, f'What is my relationship with {locationAgent.name}?', 4)
            memories.append(locationAgentMemories)

        #Choose whether or not to start a conversation
        agents, reasoning = await self.conversationStarter.StartConversation(scenario, agent, plannedActivity, locationAgents, memories)

        if agents is not None:
            #create memory that Agent decided to talk to Agent1, Agent2, etc.
            await self.memoryRepository.CreateMemory(agent, reasoning)

            #create the conversation
            conversationModel = ConversationModel(initiatingAgent = agent._id, reasoning = reasoning)
            conversationModel.agents = Enumerable(agents).select(lambda x: x._id).to_list()
            ConversationModel.objects.insert(conversationModel)

            return conversationModel, agents
        #This agent chose not to start a conversation
        return None, None

    async def CreateConversation(self, scenario, conversationModel, agents):
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
                        agentMemories.extend(await self.retrieval.RetrieveMemories(agents[i], f'What is my relationship with {agents[j].name}?', 5))
                memories.append(agentMemories)

            #create a conversation
            conversationModel = await self.conversationGenerator.CreateConversation(scenario, conversationModel, agents, plannedActivities, memories)

            if conversationModel is not None:
                #summarize the conversation for each agent
                for agent in agents:
                    #create memories for each agent
                    await self.memoryRepository.CreateMemory(agent, f"I had a conversation at {scenario.currentDateTime}: {conversationModel.summary}")
                    summaries = await self.conversationSummarizer.SummarizeConversation(agent, conversationModel)
                    if summaries is not None:
                        for summary in summaries:
                            await self.memoryRepository.CreateMemory(agent, f"{summary}")
                #save the conversation
                conversationModel.save()

    async def ConversationPipeline(self, scenario, agent):
        conversationModel, chosenAgents = await self.StartConversation(scenario, agent)
        if chosenAgents is not None and len(chosenAgents) > 1:
            return await self.CreateConversation(scenario, conversationModel, chosenAgents)
