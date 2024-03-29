from Simulation.location import Location
from Simulation.item import Item
from py_linq import *

class InteractionStream():
    def __init__(self, 
                 activityStream,
                 memoryRetrieval,
                 interactionGenerator,
                 itemRepository,
                 memoryRepository,
                 agentRepository,
                 actionGenerator,
                 locationChanger,
                 statusGenerator,
                 inventoryGenerator,
                 itemManager):
        self.activityStream = activityStream
        self.memoryRetrieval = memoryRetrieval
        self.interactionGenerator = interactionGenerator
        self.itemRepository = itemRepository
        self.memoryRepository = memoryRepository
        self.agentRepository = agentRepository
        self.actionGenerator = actionGenerator
        self.locationChanger = locationChanger
        self.statusGenerator = statusGenerator
        self.inventoryGenerator = inventoryGenerator
        self.itemManager = itemManager
        pass

    #get the agents current location
    def _findAgent(self, agent, scenario):
        location = scenario.FindAgent(agent)
        if location is None:
            location = Location("Outside", "Outdoors")
        return location
    
    #get a list of items at a location
    def _getItemsThatCanBePickedUp(self, location):
        #get a list of items in the current location
        if location.items is not None:
            availableItems = Enumerable(location.items).where(lambda x: x.canBePickedUp)
        else:
            availableItems = []
        return availableItems
    
    #get a list of items at a location
    def _getInteractiveItems(self, location):
        #get a list of items in the current location
        if location.items is not None:
            availableItems = Enumerable(location.items).where(lambda x: x.canInteract)
        else:
            availableItems = []
        return availableItems

    #get the agent's currently using item
    def _getUsingItem(self, agent):
        if agent.usingItem is None:
            usingItem = Item("Nothing", "Empty handed")
        else:
            usingItem = agent.usingItem
        return usingItem
    
    async def _moveAgent(self, agent, scenario, prevLocation, nextLocation, reasoning):
        #update the previous location
        if prevLocation is None or prevLocation.name == "Outside":
            scenario.agents.remove(agent)
        else:
            prevLocation.agents.remove(agent)

        #update the new location
        if nextLocation is None:
            #the agent is moving outside
            scenario.agents.append(agent)
        else:
            if nextLocation.agents is None:
                nextLocation.agents = []
            nextLocation.agents.append(agent)

        #persist the agent's changed location
        if nextLocation is None:
            self.agentRepository.UpdateLocation(agent, homeScenarioId=scenario._id)
            memory = f"I chose to go to outside. {reasoning}"
            await self.memoryRepository.CreateMemory(agent, memory)
        else:
            self.agentRepository.UpdateLocation(agent, homeScenarioId=scenario._id, locationId=nextLocation._id)
            #create a memory that the agent chose to move
            memory = f"I chose to go to {nextLocation.name}. {reasoning}"
            await self.memoryRepository.CreateMemory(agent, memory)
            #TODO: start the agent walking to the new location

    async def ChangeLocation(self, agent, scenario):
        location = self._findAgent(agent, scenario)

        #get the agents current planned activity
        plannedActivity = self.activityStream.GetCurrentPlannedActivity(agent, scenario.currentDateTime)
        
        #get a list of memories that are relevant to that activity
        memories = await self.memoryRetrieval.RetrieveMemories(agent, f"What is the best location to {plannedActivity.description}?")
        
        #Check if the agent wants to change locations
        chosenLocation, reasoning = await self.locationChanger.AskToChangeLocation(agent, location, plannedActivity, memories)
        if chosenLocation is not None:
            #Find the location they want to go to
            nextLocation = scenario.FindLocation(chosenLocation)
            if chosenLocation.lower() == "outside" or nextLocation is not None:
                await self._moveAgent(agent, scenario, location, nextLocation, reasoning)
                #TODO: tried to go to a nonexistent location

    async def SwapItems(self, agent, scenario):
        location = self._findAgent(agent, scenario)
        
        #Limit the available items to things that can be picked up
        availableItems = self._getItemsThatCanBePickedUp(location)
        availableItems = Enumerable(availableItems).where(lambda x: x.canBePickedUp).to_list()

        #Ask the agent if they would like to swap items
        if agent.currentItem is not None or len(availableItems) > 0:
            plannedActivity = self.activityStream.GetCurrentPlannedActivity(agent, scenario.currentDateTime)

            #get a list of memories that are relevant to that activity
            memories = await self.memoryRetrieval.RetrieveMemories(agent, f"What items would be useful for {plannedActivity.description}?")

            itemName, reasoning = await self.inventoryGenerator.ManageInventory(agent, agent.currentItem, availableItems, plannedActivity, memories)
            if itemName is not None:
                if itemName == "Drop current item":
                    if agent.currentItem is not None:
                        #The agent has chosen to drop the iotem they are currently holding... Are they also using it?
                        if agent.usingItem is not None and (agent.currentItem.name == agent.currentItem.name):
                            await self.itemManager.StopUsingItem(agent, location, None, None, reasoning)
                        await self.itemManager.DropItem(scenario, agent, location, reasoning)
                        #TODO: tried to drop an item when not holding one
                else:
                    #The agent has chosen to swap items, set their current item
                    chosenItem = Enumerable(availableItems).first_or_default(lambda x: x.name.lower() == itemName.lower())
                    if chosenItem is not None:
                        #pick up the chosen item
                        await self.itemManager.PickUpItem(chosenItem, agent, location, reasoning)
                        #TODO: tried to pick up an nonexistent or unreachable item

    async def UseItem(self, agent, scenario):
        location = self._findAgent(agent, scenario)
        availableItems = self._getInteractiveItems(location)
        plannedActivity = self.activityStream.GetCurrentPlannedActivity(agent, scenario.currentDateTime)

        #Limit the available items to things that can be interacted with
        #availableItems.append(self._getCurrentItem(agent))
        #availableItems = Enumerable(location.items).where(lambda x: x.canInteract)

        if agent.currentItem is not None or len(availableItems) > 0:

            #get a list of memories that are relevant to that activity
            memories = await self.memoryRetrieval.RetrieveMemories(agent, f"What items would be useful for {plannedActivity.description}?")
            action, itemName, itemStatus, emoji, reasoning = await self.interactionGenerator.UseItem(agent, availableItems, plannedActivity, memories)

            if action is not None:
                if action == "Stop using item":
                    await self.itemManager.StopUsingItem(agent, location, itemStatus, emoji, reasoning)
                elif action:
                    #is it the currently held item?
                    if agent.currentItem is not None and (itemName.lower() == agent.currentItem.name.lower()):
                        chosenItem = agent.currentItem
                    else:
                        chosenItem = Enumerable(availableItems).first_or_default(lambda x: x.name.lower() == itemName.lower())

                    #TODO: how effective is it to perform {action} on {item} to {plannedActivity}?

                    if chosenItem is not None:
                        await self.itemManager.UseItem(chosenItem, agent, action, location, itemStatus, emoji, reasoning)

                    #TODO: tried to use a non-existent or unreachable item

    async def SetAgentStatus(self, agent, scenario):
        location = self._findAgent(agent, scenario)
        plannedActivity = self.activityStream.GetCurrentPlannedActivity(agent, scenario.currentDateTime)

        status, emoji = await self.statusGenerator.SetStatus(scenario, agent, agent.currentItem, agent.usingItem, location, plannedActivity)
        if status is not None or emoji is not None:
            #change the agent's status
            agent.status = status
            agent.emoji = emoji

            #save out agent status
            if location.name == "Outside":
                self.agentRepository.CreateOrUpdate(agent, homeScenarioId=scenario._id)
            else:
                self.agentRepository.CreateOrUpdate(agent, homeScenarioId=scenario._id, locationId = location._id)

    async def PlanActions(self, agent, scenario):
        location = self._findAgent(agent, scenario)

        #get the agents current planned activity
        plannedActivity = self.activityStream.GetCurrentPlannedActivity(agent, scenario.currentDateTime)
        
        #get a list of memories that are relevant to that activity
        #memories = self.memoryRetrieval.RetrieveMemories(agent, f"What do I know that will help {plannedActivity.description}?")
        memories = await self.memoryRetrieval.RetrieveMemories(agent, f"What are important places for {plannedActivity.description}?", 10)
        memories.extend(await self.memoryRetrieval.RetrieveMemories(agent, f"What items would help {plannedActivity.description}?", 10))
        memories.extend(await self.memoryRetrieval.RetrieveMemories(agent, f"Who would help {plannedActivity.description}?", 10))

        #Check if the agent wants to change locations
        #result = self.actionGenerator.CreateActions(scenario.currentDateTime, agent, location, plannedActivity, memories)
        result = await self.actionGenerator.BreakDownPlannedActivity(agent, plannedActivity, memories)
        if result is not None:
            #TODO: parse the list of chosen actions?
            pass
            #Find the location they want to go to
            #nextLocation = scenario.FindLocation(result)
            #if result.lower() == "outside" or nextLocation is not None:
                #self._moveAgent(agent, scenario, location, nextLocation)
                #TODO: tried to go to a nonexistent location
        
        #TODO: take a look at this prompt from the mkturkan generative-agents repo
        #prompt = "You are {}. Your plans are: {}. You are currently in {} with the following description: {}. It is currently {}:00. The following people are in this area: {}. You can interact with them.".format(self.name, self.plans, location.name, town_areas[location.name], str(global_time), ', '.join(people))

    #TODO: Give items away?