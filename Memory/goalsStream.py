
class GoalsStream():

    def __init__(self, memoryRepository, goalsGenerator, goalRepository):
        self.memoryRepository = memoryRepository
        self.goalsGenerator = goalsGenerator
        self.goalRepository = goalRepository

    async def CreateGoals(self, agent, scenario):
        #Create appropriate goals for this character
        goals = await self.goalsGenerator.GenerateGoals(agent, scenario)

        #Store th goals in the character's memory stream
        await self.memoryRepository.CreateGoalMemories(agent, goals)

        #Store the goals in a special database for later retrieval
        for goal in goals:
            self.goalRepository.CreateGoal(goal)
