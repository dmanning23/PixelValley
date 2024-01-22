
class InventoryManager:

    def __init__(self,
                 memoryRepository,
                 agentRepository) -> None:
        self.memoryRepository = memoryRepository
        self.agentRepository = agentRepository

    def _pickUpItem(self, scenario, item, agent, location, reasoning):
        #TODO: can agents hold more than one item?
        #drop the current item
        self._dropItem(scenario, agent, location, "I tried to pick something up while already holding an item")

        #update the agent
        agent.currentItem = item

        #update the Agent in the DB
        self.agentRepository.Update(agent, homeScenarioId = scenario._id, locationId = location._id)

        #create a memory that the item was picked up
        observation = f"I picked up the {item.name} in the {location.name}. {reasoning}"
        self.memoryRepository.CreateMemory(agent, observation)

    def _dropItem(self, scenario, agent, location, reasoning):
        if agent.currentItem is not None:
            item = agent.currentItem
            #update the agent
            agent.currentItem = None

            #update the Agent in the DB
            self.agentRepository.Update(agent, homeScenarioId = scenario._id, locationId = location._id if location is not None else None)

            #TODO: some sort of item storage?

            #create a memory that the item was dropped
            observation = f"I put down the {item.name} in the {location.name}. {reasoning}"
            self.memoryRepository.CreateMemory(agent, observation)
