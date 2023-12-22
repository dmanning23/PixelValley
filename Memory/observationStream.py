class ObservationStream():

    def __init__(self, memoryRepository):
        self.memoryRepository = memoryRepository

    def CreateScenarioObservations(self, scenario):
        #Create the outside observations
        if scenario.agents is not None:
            for agent in scenario.agents:
                self.CreateAgentObservations(agent, scenario.agents, childLocations=scenario.locations)

        if scenario.locations is not None:
            for location in scenario.locations:
                self._createLocationObservations(location)

    def _createLocationObservations(self, location, parentLocation=None):
        if location.agents is not None:
            for agent in location.agents:
                self.CreateAgentObservations(agent, location.agents, location, parentLocation, location.locations)
        if location.locations is not None:
            for childLocation in location.locations:
                self._createLocationObservations(childLocation, location)

    def CreateAgentObservations(self, 
                           agent,
                           agents = None,
                           location=None,
                           parentLocation=None,
                           childLocations = None):
        
        #Generate the memory describing the location
        self._createLocationDescriptionMemories(agent, location)

        #Generate memories of all the agents in this location
        self._createAgentInLocationMemories(agent, agents, location)

        #generate memories of all the items being held by the various agents
        self._createAgentCurrentItemMemories(agent, agents)

        #generate memories of items being used by the various agents
        self._createAgentUsingItemMemories(agent, agents)

        #generate memories of all the items in this location
        self._createItemInLocationMemories(agent, location)

        #generate memories of all the items that can be picked up at this location
        self._createItemPickupMemoriesMemories(agent, location)

        #generate memories of all the items that can be interacted with at this location
        self._createItemUseMemoriesMemories(agent, location)
        
        #generate memories of the locations I can see from this one
        self._createNavigationMemories(agent, location, parentLocation, childLocations)

    def _createLocationDescriptionMemories(self, agent, location):
        if location is not None:
            observation = f"The {location.name} is {location.description}"
            self.memoryRepository.CreateMemory(agent, observation)

    def _createAgentInLocationMemories(self, agent, agents, location):
        if agents is not None:
            for locationAgent in agents:
                if agent._id == locationAgent._id:
                    observation = f"{locationAgent}"
                else:
                    observation = f"{locationAgent.name} is a {locationAgent.age} year old {locationAgent.gender}"
                self.memoryRepository.CreateMemory(agent, observation)

                if location is not None:
                    observation = f"{locationAgent.name} is in {location.name}"
                    self.memoryRepository.CreateMemory(agent, observation)
                else:
                    observation = f"{locationAgent.name} is outside"
                    self.memoryRepository.CreateMemory(agent, observation)

    def _createAgentCurrentItemMemories(self, agent, agents):
        if agents is not None:
            for locationAgent in agents:
                if locationAgent.currentItem is not None:
                    observation = f"{locationAgent.name} is holding a {locationAgent.currentItem.name}"
                    self.memoryRepository.CreateMemory(agent, observation)

    def _createAgentUsingItemMemories(self, agent, agents):
        if agents is not None:
            for locationAgent in agents:
                if locationAgent.usingItem is not None:
                    observation = f"{locationAgent.name} is using the {locationAgent.currentItem.name}"
                    self.memoryRepository.CreateMemory(agent, observation)

    def _createItemInLocationMemories(self, agent, location):
        if location is not None and location.items is not None:
            for item in location.items:
                observation = f"There is a {item.name} in {location.name}"
                self.memoryRepository.CreateMemory(agent, observation)
                observation = f"The {item.name} is {item.description}"
                self.memoryRepository.CreateMemory(agent, observation)

    def _createItemPickupMemoriesMemories(self, agent, location):
        if location is not None and location.items is not None:
            for item in location.items:
                canBePickedUp = "can" if item.canBePickedUp else "can not"
                observation = f"The {item.name} in {location.name} {canBePickedUp} be picked up"
                self.memoryRepository.CreateMemory(agent, observation)

    def _createItemUseMemoriesMemories(self, agent, location):
        if location is not None and location.items is not None:
            for item in location.items:
                canBeUsed = "can" if item.canBePickedUp else "can not"
                #TODO: this verbage is not great and will probably confuse the LLM
                observation = f"The {item.name} in {location.name} {canBeUsed} have actions applied to it"
                self.memoryRepository.CreateMemory(agent, observation)
                if item.canInteract and item.stateMachine is not None:
                    observation = f"The {item.name} in {location.name} is currently {item.stateMachine.currentState}"
                    self.memoryRepository.CreateMemory(agent, observation)

                    #Create observations of the various functions of the coffee machine
                    transitions = item.stateMachine.availableActions()
                    for transition in transitions:
                        observation = f'If the {item.name} is "{transition.startState}" and the action "{transition.action}" is applied, it will change to "{transition.targetState}"'
                        self.memoryRepository.CreateMemory(agent, observation)

    def _createNavigationMemories(self, agent, location=None, parentLocation=None, childLocations = None):
        if location is not None and parentLocation is not None:
            self._createLocationNavigationMemory(agent, location.name, parentLocation.name)

        if location is not None and parentLocation is None:
            self._createLocationNavigationMemory(agent, location.name, "outside")
        
        if location is None and childLocations is not None:
            for childLocation in childLocations:
                self._createLocationNavigationMemory(agent, "outside", childLocation.name)

        if location is not None and childLocations is not None:
            for childLocation in childLocations:
                self._createLocationNavigationMemory(agent, location.name, childLocation.name)

    def _createLocationNavigationMemory(self, agent, first, second):
        observation = f"From {first} I can get to {second}"
        self.memoryRepository.CreateMemory(agent, observation)