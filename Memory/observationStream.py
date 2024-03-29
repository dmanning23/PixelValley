import asyncio

class ObservationStream():

    def __init__(self, memoryRepository):
        self.memoryRepository = memoryRepository

    #TODO: make this whole class async

    async def CreateScenarioObservations(self, scenario):
        #Create the outside observations
        if scenario.agents is not None:
            async with asyncio.TaskGroup() as agentTasks:
                for agent in scenario.agents:
                    agentTasks.create_task(self.CreateAgentObservations(agent, scenario.agents, childLocations=scenario.locations))

        if scenario.locations is not None:
            async with asyncio.TaskGroup() as locationTasks:
                for location in scenario.locations:
                    locationTasks.create_task(self._createLocationObservations(location))

    async def _createLocationObservations(self, location, parentLocation=None):
        if location.agents is not None:
            async with asyncio.TaskGroup() as agentTasks:
                for agent in location.agents:
                    agentTasks.create_task(self.CreateAgentObservations(agent, location.agents, location, parentLocation, location.locations))
        if location.locations is not None:
            async with asyncio.TaskGroup() as locationTasks:
                for childLocation in location.locations:
                    locationTasks.create_task(self._createLocationObservations(childLocation, location))

    async def CreateAgentObservations(self, 
                           agent,
                           agents = None,
                           location=None,
                           parentLocation=None,
                           childLocations = None):
        
        #Generate the memory describing the location
        await self._createLocationDescriptionMemories(agent, location)

        #Generate memories of all the agents in this location
        await self._createAgentInLocationMemories(agent, agents, location)

        #generate memories of all the items being held by the various agents
        await self._createAgentCurrentItemMemories(agent, agents)

        #generate memories of items being used by the various agents
        await self._createAgentUsingItemMemories(agent, agents)

        #generate memories of all the items in this location
        await self._createItemInLocationMemories(agent, location)

        #generate memories of all the items that can be picked up at this location
        await self._createItemPickupMemoriesMemories(agent, location)

        #generate memories of all the items that can be interacted with at this location
        await self._createItemUseMemoriesMemories(agent, location)
        
        #generate memories of the locations I can see from this one
        await self._createNavigationMemories(agent, location, parentLocation, childLocations)

    async def _createLocationDescriptionMemories(self, agent, location):
        if location is not None:
            observation = f"The {location.name} is {location.description}"
            await self.memoryRepository.CreateMemory(agent, observation)

    async def _createAgentInLocationMemories(self, agent, agents, location):
        if agents is not None:
            for locationAgent in agents:
                if agent._id != locationAgent._id:
                    observation = f"I saw {locationAgent.name}, who is a {locationAgent.age} year old {locationAgent.gender}"
                    await self.memoryRepository.CreateMemory(agent, observation)

                #use "I" observations if the subject is the same agent
                if location is not None:
                    if agent._id != locationAgent._id:
                        observation = f"I saw that {locationAgent.name} is in {location.name}"
                    else:
                        observation = f"I am in {location.name}"
                    await self.memoryRepository.CreateMemory(agent, observation)
                else:
                    if agent._id != locationAgent._id:
                        observation = f"I saw that {locationAgent.name} is outside"
                    else:
                        observation = f"I am outside"
                    await self.memoryRepository.CreateMemory(agent, observation)

    async def _createAgentCurrentItemMemories(self, agent, agents):
        if agents is not None:
            for locationAgent in agents:
                if locationAgent.currentItem is not None:
                    if agent._id != locationAgent._id:
                        observation = f"I observed that {locationAgent.name} is holding a {locationAgent.currentItem.name}"
                    else:
                        observation = f"I am holding a {locationAgent.currentItem.name}"
                    await self.memoryRepository.CreateMemory(agent, observation)

    async def _createAgentUsingItemMemories(self, agent, agents):
        if agents is not None:
            for locationAgent in agents:
                if locationAgent.usingItem is not None:
                    if agent._id != locationAgent._id:
                        observation = f"I observed that {locationAgent.name} is using the {locationAgent.usingItem.name}"
                    else:
                        #use "I" observations when location agent matches agent
                        observation = f"I am using the {locationAgent.usingItem.name}"
                    await self.memoryRepository.CreateMemory(agent, observation)

    async def _createItemInLocationMemories(self, agent, location):
        if location is not None and location.items is not None:
            for item in location.items:
                observation = f"There is a {item.name} in {location.name}"
                await self.memoryRepository.CreateMemory(agent, observation)
                observation = f"The {item.name} is {item.description}"
                await self.memoryRepository.CreateMemory(agent, observation)

    async def _createItemPickupMemoriesMemories(self, agent, location):
        if location is not None and location.items is not None:
            for item in location.items:
                canBePickedUp = "can" if item.canBePickedUp else "can not"
                observation = f"The {item.name} in {location.name} {canBePickedUp} be picked up"
                await self.memoryRepository.CreateMemory(agent, observation)

    async def _createItemUseMemoriesMemories(self, agent, location):
        if location is not None and location.items is not None:
            for item in location.items:
                canBeUsed = "can" if item.canBePickedUp else "can not"
                #TODO: this verbage is not great and will probably confuse the LLM
                observation = f"The {item.name} in {location.name} {canBeUsed} have actions applied to it"
                await self.memoryRepository.CreateMemory(agent, observation)
                if item.canInteract and item.stateMachine is not None:
                    observation = f"The {item.name} in {location.name} is currently {item.stateMachine.currentState}"
                    await self.memoryRepository.CreateMemory(agent, observation)

                    #Create observations of the various functions of the coffee machine
                    transitions = item.stateMachine.availableActions()
                    for transition in transitions:
                        observation = f'If the {item.name} is "{transition.startState}" and the action "{transition.action}" is applied, it will change to "{transition.targetState}"'
                        await self.memoryRepository.CreateMemory(agent, observation)

    async def _createNavigationMemories(self, agent, location=None, parentLocation=None, childLocations = None):
        if location is not None and parentLocation is not None:
            await self._createLocationNavigationMemory(agent, location.name, parentLocation.name)

        if location is not None and parentLocation is None:
            await self._createLocationNavigationMemory(agent, location.name, "outside")
        
        if location is None and childLocations is not None:
            for childLocation in childLocations:
                await self._createLocationNavigationMemory(agent, "outside", childLocation.name)

        if location is not None and childLocations is not None:
            for childLocation in childLocations:
                await self._createLocationNavigationMemory(agent, location.name, childLocation.name)

    async def _createLocationNavigationMemory(self, agent, first, second):
        observation = f"From {first} I can get to {second}"
        await self.memoryRepository.CreateMemory(agent, observation)