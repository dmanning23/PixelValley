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
                 actionGenerator):
        self.activityStream = activityStream
        self.memoryRetrieval = memoryRetrieval
        self.interactionGenerator = interactionGenerator
        self.itemRepository = itemRepository
        self.memoryRepository = memoryRepository
        self.agentRepository = agentRepository
        self.actionGenerator = actionGenerator
        pass

    #get the agents current location
    def _findAgent(self, agent, scenario):
        location = scenario.FindAgent(agent)
        if location is None:
            location = Location("Outside", "Outdoors")
        return location
    
    #get a list of items at a location
    def _getAvailableItems(self, location):
        #get a list of items in the current location
        if location.items is not None:
            availableItems = Enumerable(location.items).where(lambda x: x.canBePickedUp)
        else:
            availableItems = []
        return availableItems

    #get the agent's currently held item
    def _getCurrentItem(self, agent):
        if agent.currentItem is None:
            currentItem = Item("Nothing", "Empty handed")
        else:
            currentItem = agent.currentItem
        return currentItem
    
    #get the agent's currently using item
    def _getUsingItem(self, agent):
        if agent.usingItem is None:
            usingItem = Item("Nothing", "Empty handed")
        else:
            usingItem = agent.usingItem
        return usingItem
    
    def _moveAgent(self, agent, scenario, prevLocation, nextLocation):
        #update the previous location
        if prevLocation is not None:
            prevLocation.agents.remove(agent)
        else:
            scenario.agents.remove(agent)

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
            self.agentRepository.Update(agent, homeScenarioId=scenario._id)
        else:
            self.agentRepository.Update(agent, homeScenarioId=scenario._id, locationId=nextLocation._id)
        #TODO: create observations? or wait until the next timestep?
        #TODO: if the agent is using an item, stop using it and create a memory
        #TODO: start the agent walking to the new location

        pass
    
    def _dropItem(self, item, agent, location):
        #update the agent
        agent.currentItem = None

        #change the item's location
        if location.items is None:
            location.items = []
        location.items.append(item)
        #TODO: what happens when the agent tries to drop something outside?

        #update in the DB
        self.itemRepository.Update(item, location._id, None)

        #create a memory that the item was dropped
        observation = f"I put down the {item.name} in the {location.name}"
        self.memoryRepository.CreateMemory(agent, observation)

    def _pickUpItem(self, item, agent, location):
        #update the agent
        agent.currentItem = item

        #change the item's location
        location.items.remove(item)

        #update in the DB
        self.itemRepository.Update(item, None, agent._id)

        #create a memory that the item was picked up
        observation = f"I picked up the {item.name} in the {location.name}"
        self.memoryRepository.CreateMemory(agent, observation)

    def _useItem(self, item, agent, action):
        #update the agent
        agent.usingItem = item

        #apply the action
        result = item.stateMachine.sendMessage(action)

        if result:
            #update in the DB
            self.itemRepository.Update()
            observation = f"I successfully performed the action {action} on the {item.name}, and changed its state to {item.stateMachine.currentState}"
            self.memoryRepository.CreateMemory(observation)
        else:
            observation = f"I performed the action {action} on the {item.name} while it was {item.stateMachine.currentState}, but nothing happened."
            self.memoryRepository.CreateMemory(observation)

    def _stopUsingItem(self, item, agent):
        #update the agent
        agent.usingItem = None

        #TODO: how is this info stored?

    def ChangeLocation(self, agent, scenario):
        location = self._findAgent(agent, scenario)

        #get the agents current planned activity
        plannedActivity = self.activityStream.GetCurrentPlannedActivity(agent, scenario.currentDateTime)
        
        #get a list of memories that are relevant to that activity
        memories = self.memoryRetrieval.RetrieveMemories(agent, f"What is the best location to {plannedActivity.description}?")
        
        #Check if the agent wants to change locations
        result = self.interactionGenerator.AskToChangeLocation(agent, location, plannedActivity, memories)
        if result is not None:
            #Find the location they want to go to
            nextLocation = scenario.FindLocation(result)
            if result.lower() == "outside" or nextLocation is not None:
                self._moveAgent(agent, scenario, location, nextLocation)
                #TODO: tried to go to a nonexistent location

    def SwapItems(self, agent, scenario):
        location = self._findAgent(agent, scenario)
        currentItem = self._getCurrentItem(agent)
        plannedActivity = self.activityStream.GetCurrentPlannedActivity(agent, scenario.currentDateTime)

        #Limit the available items to things that can be picked up
        availableItems = self._getAvailableItems(location)
        availableItems = Enumerable(availableItems).where(lambda x: x.canBePickedUp)

        #Ask the agent if they would like to swap items
        if currentItem.name != "Nothing" or len(availableItems) > 0:
            result = self.interactionGenerator.AskToChangeItem(agent, currentItem, availableItems, plannedActivity)
            if result is not None:
                if result == "Drop current item":
                    if agent.currentItem is not None:
                        self._dropItem(agent.currentItem, agent, location)
                        #TODO: tried to drop an item when not holding one
                else:
                    #The agent has chosen to swap items, set their current item
                    chosenItem = Enumerable(availableItems).first_or_default(lambda x: x.name.lower() == result.lower())
                    if chosenItem is not None:
                        #drop the current item
                        if agent.currentItem is not None:
                            self._dropItem(agent.currentItem, agent, location)
                        #pick up the chosen item
                        self._pickUpItem(chosenItem, agent, location)
                        #TODO: tried to pick up an nonexistent or unreachable item

    def UseItem(self, agent, scenario):
        location = self._findAgent(agent, scenario)
        availableItems = self._getAvailableItems(location)
        usingItem = self._getUsingItem(agent)
        plannedActivity = self.activityStream.GetCurrentPlannedActivity(agent, scenario.currentDateTime)

        #Limit the available items to things that can be interacted with
        availableItems.append(self._getCurrentItem(agent))
        availableItems = Enumerable(location.items).where(lambda x: x.canInteract)

        #test the location changer!
        if usingItem.name != "Nothing" or len(availableItems) > 0:
            result = self.interactionGenerator.AskToUseItem(agent, usingItem, availableItems, plannedActivity)

            if result == "Stop using item":
                self._stopUsingItem(agent,)
            if result is not None:
                chosenItem = Enumerable(availableItems).first_or_default(lambda x: x.name.lower() == result.lower())
                if chosenItem is not None:
                    agent.usingItem = chosenItem

                    #Find out what the agent knows about that item
                    memories = self.memoryRetrieval.RetrieveMemories(agent, f"What do I know about actions that can be applied to {result}?")
                    
                    #Ask the agent what they want to do with the item
                    action = self.interactionGenerator.PerformItemAction(agent, chosenItem, plannedActivity, memories)
                    if action is not None:
                        self._useItem(chosenItem, agent, action)
                        #TODO: tried to use a non-existent or unreachable item

    def SetAgentStatus(self, agent, scenario):
        location = self._findAgent(agent, scenario)
        plannedActivity = self.activityStream.GetCurrentPlannedActivity(agent, scenario.currentDateTime)
        usingItem = self._getUsingItem(agent)
        currentItem = self._getCurrentItem(agent)

        status = self.interactionGenerator.AskToSetStatus(agent, currentItem, usingItem, location, plannedActivity)
        if status is not None:
            #change the agent's status
            agent.status = status
            #save out agent status
            if location.name == "Outside":
                self.agentRepository.CreateOrUpdate(agent, homeScenarioId=scenario._id)
            else:
                self.agentRepository.CreateOrUpdate(agent, homeScenarioId=scenario._id, locationId = location._id)

    def PlanActions(self, agent, scenario):
        location = self._findAgent(agent, scenario)

        #get the agents current planned activity
        plannedActivity = self.activityStream.GetCurrentPlannedActivity(agent, scenario.currentDateTime)
        
        #get a list of memories that are relevant to that activity
        #memories = self.memoryRetrieval.RetrieveMemories(agent, f"What do I know that will help {plannedActivity.description}?")
        memories = self.memoryRetrieval.RetrieveMemories(agent, f"What are important places for {plannedActivity.description}?", 10)
        memories.extend(self.memoryRetrieval.RetrieveMemories(agent, f"What items would help {plannedActivity.description}?", 10))
        memories.extend(self.memoryRetrieval.RetrieveMemories(agent, f"Who would help {plannedActivity.description}?", 10))

        #Check if the agent wants to change locations
        #result = self.actionGenerator.CreateActions(scenario.currentDateTime, agent, location, plannedActivity, memories)
        result = self.actionGenerator.BreakDownPlannedActivity(agent, plannedActivity, memories)
        if result is not None:
            #TODO: parse the list of chosen actions?
            pass
            #Find the location they want to go to
            #nextLocation = scenario.FindLocation(result)
            #if result.lower() == "outside" or nextLocation is not None:
                #self._moveAgent(agent, scenario, location, nextLocation)
                #TODO: tried to go to a nonexistent location