from random import *
from mongoengine import *
from py_linq import *

from Simulation.timeStream import TimeStream

from Models.agentDescriptionModel import AgentDescriptionModel

from Generators.scenarioGenerator import ScenarioGenerator
from Generators.locationGenerator import LocationGenerator
from Generators.itemGenerator import ItemGenerator
from Generators.agentGenerator import AgentGenerator
from Generators.goalsGenerator import GoalsGenerator
from Generators.plannedActivityGenerator import PlannedActivityGenerator
from Generators.characterDescriptionGenerator import CharacterDescriptionGenerator

from Repository.scenarioRepository import ScenarioRepository
from Repository.locationRepository import LocationRepository
from Repository.agentRepository import AgentRepository
from Repository.itemRepository import ItemRepository
from Repository.goalsRepository import GoalsRepository
from Repository.simulationRepository import SimulationRepository

from Memory.memoryRepository import MemoryRepository
from Memory.observationStream import ObservationStream
from Memory.retrievalStream import RetrievalStream
from Memory.reflectionGenerator import ReflectionGenerator
from Memory.reflectionStream import ReflectionStream
from Memory.goalsStream import GoalsStream
from Memory.plannedActivityStream import PlannedActivityStream

from Interactions.interactionGenerator import InteractionGenerator
from Interactions.interactionStream import InteractionStream
from Interactions.actionGenerator import ActionGenerator
from Interactions.locationChanger import LocationChanger
from Interactions.statusGenerator import StatusGenerator
from Interactions.inventoryGenerator import InventoryGenerator
from Interactions.itemManager import ItemManager

from ConversationEngine.conversationGenerator import ConversationGenerator
from ConversationEngine.conversationStream import ConversationStream
from ConversationEngine.conversationSummarizer import ConversationSummarizer
from ConversationEngine.conversationStarter import ConversationStarter

from AssetCreation.characterPortraitGenerator import CharacterPortraitGenerator
from AssetCreation.buildingExteriorGenerator import BuildingExteriorGenerator
from AssetCreation.buildingInteriorGenerator import BuildingInteriorGenerator
from AssetCreation.backgroundGenerator import BackgroundGenerator
from AssetCreation.characterIconGenerator import CharacterIconGenerator
from AssetCreation.characterChibiGenerator import CharacterChibiGenerator
from AssetCreation.assetManager import AssetManager

class Simulator:

    def FetchScenario(self, userId, scenarioId):
        
        #load up the scenario
        scenario = ScenarioRepository.Get(userId, scenarioId)

        #load the locations
        scenario.locations = LocationRepository.FetchScenario(scenario._id)

        #load the items
        for location in scenario.locations:
            ItemRepository.FetchLocation(location)

        #load the agents
        #load the agents into the scenario
        scenario.agents = AgentRepository.GetOutsideAgents(scenario._id)
        #load the agents into all the locations
        for location in scenario.locations:
            AgentRepository.FetchLocation(location)

        #load up the agent's items
        agents = scenario.GetAgents()
        for agent in agents:

            #load up the items that are being used
            items = ItemRepository.GetItems(usingCharacterId=agent._id)
            if items is not None and len(items) > 0:
                agent.usingItem = items[0]

        #store the scenario
        return scenario

    def CreateScenario(self, userId, scenarioDescription):

        #expand the setting
        settingGen = ScenarioGenerator()
        scenario = settingGen.GenerateScenario(scenarioDescription)

        #create the initial list of locations
        locationGen = LocationGenerator()
        scenario.locations = locationGen.Generate(scenario)

        #decompose each location into children if application
        for location in scenario.locations:
            locationGen.GenerateChildLocations(location)

        items = []
        itemGen = ItemGenerator()
        for location in scenario.locations:
            items = items + itemGen.PopulateLocations(location)

        for item in items:
            #We aren't using finite state machines in the final product.
            #itemGen.GenerateFiniteStateMachine(item)
            pass

        #create all the villagers
        agentGen = AgentGenerator()
        agents = agentGen.GenerateCharacters(scenario)
        #place each villager somewhere
        for agent in agents:
            #put the agent outside?
            isOutside = randint(0, 3)
            if isOutside < 1:
                if scenario.agents is None:
                    scenario.agents = []
                scenario.agents.append(agent)
            else:
                #get a random location
                locationIndex = randint(0, len(scenario.locations) - 1)
                #make sure there is an agent list
                if scenario.locations[locationIndex].agents is None:
                    scenario.locations[locationIndex].agents = []
                #add to the agent list
                scenario.locations[locationIndex].agents.append(agent)

        simulationRepository = SimulationRepository()
        simulationRepository.SaveScenario(userId, scenario)
        simulationRepository.SaveLocations(scenario)
        simulationRepository.SaveItems(scenario)
        simulationRepository.SaveAgents(scenario)

        return scenario

    def InitializeScenario(self, userId, scenario):
        memRepo = MemoryRepository()
        obsStream = ObservationStream(memRepo)
        goalRepo = GoalsRepository()
        goalGen = GoalsGenerator()
        goalsStream = GoalsStream(memRepo, goalGen, goalRepo)
        retrieval = RetrievalStream(memRepo)
        activityGen = PlannedActivityGenerator()
        activityStream = PlannedActivityStream(memRepo, activityGen, goalRepo, retrieval)

        characterPortraitGenerator = CharacterPortraitGenerator()
        buildingExteriorGenerator = BuildingExteriorGenerator()
        buildingInteriorGenerator = BuildingInteriorGenerator()
        backgroundGenerator = BackgroundGenerator()
        characterIconGenerator = CharacterIconGenerator()
        characterDescriptionGenerator = CharacterDescriptionGenerator()
        characterChibiGenerator = CharacterChibiGenerator()
        assetManager = AssetManager()

        #Create some observational memories
        obsStream.CreateScenarioObservations(scenario)

        #Create the agent goals
        for agent in scenario.GetAgents():
                goalsStream.CreateGoals(agent, scenario)

        #Create the agent's daily plans
        for agent in scenario.GetAgents():
            activityStream.CreatePlannedActivities(agent, scenario)

        #Populate all the artwork
        assetManager.CreateScenarioBackground(userId, scenario, backgroundGenerator)
        assetManager.PopulateMissingBuildingExteriors(scenario, buildingExteriorGenerator)
        assetManager.PopulateMissingBuildingInteriors(scenario, buildingInteriorGenerator)
        assetManager.PopulateMissingCharacterDescriptions(scenario, characterDescriptionGenerator)
        assetManager.PopulateMissingCharacterProfile(scenario, characterPortraitGenerator)
        assetManager.PopulateMissingCharacterIcons(scenario, characterIconGenerator)
        assetManager.PopulateMissingCharacterChibis(scenario, characterChibiGenerator)

        #Verify all those creates worked
        assetManager.CreateScenarioBackground(userId, scenario, backgroundGenerator)
        assetManager.PopulateMissingBuildingExteriors(scenario, buildingExteriorGenerator)
        assetManager.PopulateMissingBuildingInteriors(scenario, buildingInteriorGenerator)
        assetManager.PopulateMissingCharacterDescriptions(scenario, characterDescriptionGenerator)
        assetManager.PopulateMissingCharacterProfile(scenario, characterPortraitGenerator)
        assetManager.PopulateMissingCharacterIcons(scenario, characterIconGenerator)
        assetManager.PopulateMissingCharacterChibis(scenario, characterChibiGenerator)

        assetManager.UploadToS3(scenario)

    def AdvanceScenario(self, userId, scenario):
        memRepo = MemoryRepository()
        obsStream = ObservationStream(memRepo)
        goalRepo = GoalsRepository()
        retrieval = RetrievalStream(memRepo)
        reflectionGen = ReflectionGenerator(memRepo, retrieval)

        activityGen = PlannedActivityGenerator()
        activityStream = PlannedActivityStream(memRepo, activityGen, goalRepo, retrieval)
        interactionGen = InteractionGenerator()
        itemRepo = ItemRepository()
        agentRepo = AgentRepository()
        reflectionStream = ReflectionStream(memRepo, reflectionGen, agentRepo)
        actionGenerator = ActionGenerator()
        conversationGenerator = ConversationGenerator()
        locationChanger = LocationChanger()
        conversationSummarizer = ConversationSummarizer()
        conversationStarter = ConversationStarter()
        conversationStream = ConversationStream(conversationGenerator,
                                                activityStream,
                                                retrieval,
                                                memRepo,
                                                conversationSummarizer,
                                                conversationStarter)
        statusGenerator = StatusGenerator()
        inventoryGenerator = InventoryGenerator()
        itemManager = ItemManager(memRepo,
                                agentRepo,
                                itemRepo)
        iteractionStream = InteractionStream(activityStream,
                                            retrieval,
                                            interactionGen,
                                            itemRepo,
                                            memRepo,
                                            agentRepo,
                                            actionGenerator,
                                            locationChanger,
                                            statusGenerator,
                                            inventoryGenerator,
                                            itemManager)
        timeStream = TimeStream()

        #increment the time for each agent
        timeStream.IncrementTime(userId, scenario)

        #TODO: if the day has turned over, create planned actions for the day

        #Create some observational memories
        obsStream.CreateScenarioObservations(scenario)

        #Reflect if so desired
        for agent in scenario.GetAgents():
            reflectionStream.TriggerReflection(agent)

        #Interactions!
        #Move?
        for agent in scenario.GetAgents():
            iteractionStream.ChangeLocation(agent, scenario)

        #Pick an item up?
        for agent in scenario.GetAgents():
            iteractionStream.SwapItems(agent, scenario)

        #Use an item?
        for agent in scenario.GetAgents():
            iteractionStream.UseItem(agent, scenario)

        #Talk to another agent
        for agent in scenario.GetAgents():
            conversationStream.ConversationPipeline(scenario, agent)

        for agent in scenario.GetAgents():
            iteractionStream.SetAgentStatus(agent, scenario)
