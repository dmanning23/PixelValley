
class ReflectionStream:

    _reflectionTriggerThreshold = 150.0

    def __init__(self,
                 memoryRetrieval,
                 reflectionGenerator) -> None:
        self.memoryRetrieval = memoryRetrieval
        self.reflectionGenerator = reflectionGenerator

    def TriggerReflection(self, scenario, agent, location):
        #get the memories since last reflection
        memories = self.memoryRetrieval.GetMemoriesSinceTimestamp(agent.timeOfLastReflection)

        #Sum the importance of the memories
        sum = 0.0
        for memory in memories:
            sum += memory.importance

        #has it passed the threshold?
        if sum >= _reflectionTriggerThreshold:

        #Trigger a reflection

        pass