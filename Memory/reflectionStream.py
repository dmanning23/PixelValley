
class ReflectionStream:

    _reflectionTriggerThreshold = 100.0

    def __init__(self,
                 memoryRepository,
                 reflectionGenerator,
                 agentRepository) -> None:
        self.memoryRepository = memoryRepository
        self.reflectionGenerator = reflectionGenerator
        self.agentRepository = agentRepository

    def TriggerReflection(self, agent):
        #get the memories since last reflection
        memories = self.memoryRepository.GetMemoriesSinceTimestamp(agent, agent.timeOfLastReflection)

        #Sum the importance of the memories
        sum = 0.0
        for memory in memories:
            sum += memory.importance

        #has it passed the threshold?
        if sum >= self._reflectionTriggerThreshold:
            #Trigger a reflection
            self.reflectionGenerator.CreateReflections(agent)
            #update the agent "time since reflection"
            agent.timeOfLastReflection = agent.currentTime
            self.agentRepository.Update(agent)
