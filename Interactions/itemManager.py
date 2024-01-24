
class ItemManager:

    def __init__(self,
                 memoryRepository,
                 agentRepository,
                 itemRepository) -> None:
        self.memoryRepository = memoryRepository
        self.agentRepository = agentRepository
        self.itemRepository = itemRepository

    def PickUpItem(self, item, agent, location, reasoning):
        #TODO: can agents hold more than one item?
        #drop the current item
        self.DropItem(agent, location, "I tried to pick something up while already holding an item")

        #update the agent
        agent.currentItem = item

        #update the Agent in the DB
        self.agentRepository.Update(agent)

        #create a memory that the item was picked up
        observation = f"I picked up the {item.name} in the {location.name}. {reasoning}"
        self.memoryRepository.CreateMemory(agent, observation)

    def DropItem(self, agent, location, reasoning):
        if agent.currentItem is not None:
            item = agent.currentItem
            #update the agent
            agent.currentItem = None

            #update the Agent in the DB
            self.agentRepository.Update(agent)

            #TODO: some sort of item storage?

            #is teh character using the held item?
            if agent.IsUsingHeldItem():
                self.StopUsingItem(agent, location, "", "", f"I was using the {item.name} but put it down, so it is no longer in use.")

            #create a memory that the item was dropped
            if location is None:
                observation = f"I put down the {item.name}. {reasoning}"
            else:
                observation = f"I put down the {item.name} in the {location.name}. {reasoning}"
            self.memoryRepository.CreateMemory(agent, observation)

    def UseItem(self, item, agent, action, location, itemStatus, emoji, reasoning):

        #TODO: is the item currently in use?

        if (agent.currentItem is not None and (item.name == agent.currentItem.name)):
            #the held item has to be updated in the agent
            agent.currentItem.status = itemStatus
            agent.currentItem.emoji = emoji
            item = agent.currentItem
            agent.usingItem = agent.currentItem
            self.agentRepository.Update(agent)
        else:
            item.status = itemStatus
            item.emoji = emoji
            agent.usingItem = item
            #update in the DB
            self.itemRepository.Update(item, locationId=location._id, usingCharacterId=agent._id)

        observation = f"I performed the action {action} on the {item.NameWithStatus()}. {reasoning}"
        self.memoryRepository.CreateMemory(agent, observation)

    def StopUsingItem(self, agent, location, itemStatus, emoji, reasoning):
        if agent.usingItem is not None:
            #Are the using and held item the same?
            if (agent.currentItem is not None and (agent.usingItem.name == agent.currentItem.name)):
                #the held item has to be updated in the agent
                agent.usingItem = None
                agent.currentItem.status = itemStatus
                agent.currentItem.emoji = emoji
                item = agent.currentItem
                self.agentRepository.Update(agent)
            else:
                item = agent.usingItem
                agent.usingItem = None
                item.status = itemStatus
                item.emoji = emoji
                self.itemRepository.Update(item, locationId=location._id)

            #create the memory
            self.memoryRepository.CreateMemory(agent, f"I stopped using the {item.NameWithStatus()}. {reasoning}")