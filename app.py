import os
import streamlit as st
from keys import openAIapikey
from keys import mongoUri
from keys import cloudFrontUri
from random import *
from mongoengine import *
from py_linq import *
import time
import asyncio

from Simulation.timeStream import TimeStream
from Simulation.simulator import Simulator

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
from AssetCreation.s3Uploader import *

def main():

    #Set up the api key for OpenAI
    os.environ["OPENAI_API_KEY"] = openAIapikey

    #spin up mongoDB
    connect(host=mongoUri, db="pixelValley") #connect for mongoengine

    asyncio.run(initializeScenario())

def clearSession():
    st.session_state["scenario"]=None

async def initializeScenario():
    userId = st.session_state["userId"]

    if "scenario" in st.session_state and st.session_state['scenario'] is not None:
        scenario = st.session_state["scenario"]
        await displayScenario(userId, scenario)

    else:
        st.subheader("Select an existing scenario, or create a new one")

        #Get the user's scenarios
        userId = st.session_state["userId"]
        scenarios = ScenarioRepository.GetScenarios(userId)
        if scenarios:
            selectContainer = st.container()
            with selectContainer:
                with st.form(key="select scenario", clear_on_submit=True):
                    selectedScenario  = st.selectbox("Select an existing scenario:",
                                                     scenarios,
                                                     format_func=lambda x: x.name)
                    select_button = st.form_submit_button(label="Select")
                    if select_button:
                        fetchScenario(userId, selectedScenario._id)

        createContainer = st.container()
        with createContainer:
            with st.form(key="create scenario", clear_on_submit=True):
                user_input  = st.text_area(label="Enter a short description of the scenario: ", key="input", height = 100)
                create_button = st.form_submit_button(label="Create")

                if create_button:
                    if not user_input:
                        user_input = f"A cozy little village"
                    await createScenario(userId, user_input)

            with st.form(key="big create", clear_on_submit=True):
                user_input  = st.text_area(label="Enter a short description of the scenario: ", key="bigInput", height = 100)
                create_button = st.form_submit_button(label="Big Create")

                if create_button:
                    if not user_input:
                        user_input = f"A cozy little village"
                    await bigCreate(userId, user_input)

def fetchScenario(userId, scenarioId):
    
    #load up the scenario
    with st.spinner("Loading scenario..."):
        scenario = ScenarioRepository.Get(userId, scenarioId)

    #load the locations
    with st.spinner("Loading locations..."):
        scenario.locations = LocationRepository.FetchScenario(scenario._id)

    #load the items
    with st.spinner("Loading items..."):
        for location in scenario.locations:
            ItemRepository.FetchLocation(location)

    #load the agents
    with st.spinner("Loading agents..."):
        #load the agents into the scenario
        scenario.agents = AgentRepository.GetOutsideAgents(scenario._id)
        #load the agents into all the locations
        for location in scenario.locations:
            AgentRepository.FetchLocation(location)

    #load up the agent's items
    with st.spinner("Loading agent items..."):
        agents = scenario.GetAgents()
        for agent in agents:

             #load up the items that are being used
            items = ItemRepository.GetItems(usingCharacterId=agent._id)
            if items is not None and len(items) > 0:
                agent.usingItem = items[0]

    #store the scenario
    st.session_state["scenario"] = scenario
    st.rerun()

def createScenario(userId, scenarioDescription):
    with st.spinner("Creating scenario..."):
        #expand the setting
        settingGen = ScenarioGenerator()
        scenario = settingGen.GenerateScenario(scenarioDescription)

    with st.spinner("Populating locations..."):
        #create the initial list of locations
        locationGen = LocationGenerator()
        scenario.locations = locationGen.Generate(scenario)

        #decompose each location into children if application
        for location in scenario.locations:
            locationGen.GenerateChildLocations(location)

        items = []
        itemGen = ItemGenerator()
        for location in scenario.locations:
            with st.spinner(F"Populating items for {location.name}..."):
                items = items + itemGen.PopulateLocations(location)
                pass

    with st.spinner("Reticulating splines..."):
        for item in items:
            #We aren't using finite state machines in the final product.
            #itemGen.GenerateFiniteStateMachine(item)
            pass

    #create all the villagers
    with st.spinner("Creating villagers..."):
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

    #Store the scenario
    simulationRepository = SimulationRepository()
    with st.spinner("Saving scenario..."):
        simulationRepository.SaveScenario(userId, scenario)

    with st.spinner("Saving locations..."):
        simulationRepository.SaveLocations(scenario)

    with st.spinner("Saving items..."):
        simulationRepository.SaveItems(scenario)

    with st.spinner("Saving villagers..."):
        simulationRepository.SaveAgents(scenario)

    #store the scenario
    st.session_state["scenario"] = scenario
    st.rerun()

async def bigCreate(userId, scenarioDescription):
    simulator = Simulator()
    with st.spinner("Running the Big Create..."):
        scenario = await simulator.CreateScenario(userId, scenarioDescription)
    with st.spinner("Initializing the scenario..."):
        await simulator.InitializeScenario(userId, scenario)
    st.session_state["scenario"] = scenario
    st.rerun()

async def displayScenario(userId, scenario):

    memRepo = MemoryRepository()
    obsStream = ObservationStream(memRepo)
    goalRepo = GoalsRepository()
    retrieval = RetrievalStream(memRepo)
    reflectionGen = ReflectionGenerator(memRepo, retrieval)

    goalGen = GoalsGenerator()
    goalsStream = GoalsStream(memRepo, goalGen, goalRepo)
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
    characterPortraitGenerator = CharacterPortraitGenerator()
    buildingExteriorGenerator = BuildingExteriorGenerator()
    buildingInteriorGenerator = BuildingInteriorGenerator()
    backgroundGenerator = BackgroundGenerator()
    characterIconGenerator = CharacterIconGenerator()
    characterDescriptionGenerator = CharacterDescriptionGenerator()
    characterChibiGenerator = CharacterChibiGenerator()
    assetManager = AssetManager()
    simulationRepository = SimulationRepository()
    simulator = Simulator()
    
    clear_button = st.button(label="Clear memory")
    if clear_button:
        memRepo.collection.delete_many({"time": { "$lt": 10 }})

    #increment the time for each agent
    time_button = st.button(label="Increment Time")
    if time_button:
        timeStream.IncrementTime(userId, scenario)

    #Run an update loop
    update_button = st.button(label="Run Update Loop")
    if update_button:
        t0 = time.time()
        await simulator.AdvanceScenario(userId, scenario)
        t1 = time.time()
        elapsedTime = {t1-t0}
        st.header(f"Elapsed time: {elapsedTime}")
        print(f"Total time: {elapsedTime}")

    createContainer = st.container()
    with createContainer:
        #Create some observational memories
        observe_button = st.button(label="Create Observations")
        if observe_button:
            #make some observations
            await obsStream.CreateScenarioObservations(scenario)

        reflect_button = st.button(label="Create Reflections")
        if reflect_button:
            for agent in scenario.GetAgents():
                await reflectionGen.CreateReflections(agent)

        trigger_reflections_button = st.button(label="Trigger Reflections?")
        if trigger_reflections_button:
            for agent in scenario.GetAgents():
                await reflectionStream.TriggerReflection(agent)

        goals_button = st.button(label="Create Goals")
        if goals_button:
            for agent in scenario.GetAgents():
                await goalsStream.CreateGoals(agent, scenario)

        plans_button = st.button(label="Create Daily Planned Activities")
        if plans_button:
            for agent in scenario.GetAgents():
                await activityStream.CreatePlannedActivities(agent, scenario)

    itemContainer = st.container()
    with itemContainer:
        change_item_button = st.button(label="Swap Items?")
        if change_item_button:
            for agent in scenario.GetAgents():
                await iteractionStream.SwapItems(agent, scenario)

        item_interaction_button = st.button(label="Use an item?")
        if item_interaction_button:
            for agent in scenario.GetAgents():
                await iteractionStream.UseItem(agent, scenario)

    interactionContainer = st.container()
    with interactionContainer:

        change_location_button = st.button(label="Change Agent Locations?")
        if change_location_button:
            for agent in scenario.GetAgents():
                await iteractionStream.ChangeLocation(agent, scenario)

        agent_status_button = st.button(label="Set Agent statuses")
        if agent_status_button:
            for agent in scenario.GetAgents():
                await iteractionStream.SetAgentStatus(agent, scenario)

        action_button = st.button(label="Plan actions")
        if action_button:
            for agent in scenario.GetAgents():
                await iteractionStream.PlanActions(agent, scenario)

    conversationContainer = st.container()
    with conversationContainer:

        choose_conversation_button = st.button(label="Choose conversation")
        if choose_conversation_button:
            agents = scenario.GetAgents()
            conversation, agents = await conversationStream.StartConversation(scenario, agents[0])

        conversation_button2 = st.button(label="Have conversation")
        if conversation_button2:
            #get the list of agents
            agents = scenario.GetAgents()
            conversationAgents = [ agents[0], agents[1] ]
            await conversationStream.CreateConversation(scenario, conversationAgents)

        conversation_button3 = st.button(label="Have group conversation")
        if conversation_button3:
            #get the list of agents
            agents = scenario.GetAgents()
            conversationAgents = [ agents[0], agents[1], agents[2] ]
            await conversationStream.CreateConversation(scenario, conversationAgents)

        conversation_button4 = st.button(label="Conversation Pipeline!")
        if conversation_button4:
            agents = scenario.GetAgents()
            conversation = await conversationStream.ConversationPipeline(scenario, agents[0])

    assetContainer = st.container()
    with assetContainer:
        profilePic_button = st.button(label="Populate missing profile pictures")
        if profilePic_button:
            await assetManager.PopulateMissingCharacterDescriptions(scenario, characterDescriptionGenerator)
            assetManager.PopulateMissingCharacterProfile(scenario, characterPortraitGenerator)

        #TODO: move agent images to description
            
        icon_button = st.button(label="Populate missing character icons")
        if icon_button:
            await assetManager.PopulateMissingCharacterDescriptions(scenario, characterDescriptionGenerator)
            assetManager.PopulateMissingCharacterIcons(scenario, characterIconGenerator)

        icon_button = st.button(label="Populate missing character chibis")
        if icon_button:
            await assetManager.PopulateMissingCharacterDescriptions(scenario, characterDescriptionGenerator)
            assetManager.PopulateMissingCharacterChibis(scenario, characterChibiGenerator)

        buildingExterior_button = st.button(label="Populate missing building exteriors")
        if buildingExterior_button:
            assetManager.PopulateMissingBuildingExteriors(scenario, buildingExteriorGenerator)

        buildingInterior_button = st.button(label="Populate missing building interiors")
        if buildingInterior_button:
            assetManager.PopulateMissingBuildingInteriors(scenario, buildingInteriorGenerator)

        buildingExterior_button = st.button(label="Redo building exteriors")
        if buildingExterior_button:
            for location in scenario.locations:
                location.imageFilename, location.resizedImageFilename = buildingExteriorGenerator.CreateLocation(location, scenario)
            simulationRepository.SaveLocations(scenario)

        background_button = st.button(label="Create scenario background")
        if background_button:
            assetManager.CreateScenarioBackground(userId, scenario, backgroundGenerator)

        describe_character = st.button(label="Create character descriptions")
        if describe_character:
            for agent in scenario.GetAgents():
                result = await characterDescriptionGenerator.DescribeCharacter(agent)
                result.agentId = agent._id
                AgentDescriptionModel.objects.insert(result)

        characterDescriptions_button = st.button(label="Populate missing character descriptions")
        if characterDescriptions_button:
            await assetManager.PopulateMissingCharacterDescriptions(scenario, characterDescriptionGenerator)

        populateMissingCharacterArtwork_button = st.button(label="Populate all missing character artwork")
        if populateMissingCharacterArtwork_button:
            await assetManager.PopulateMissingCharacterDescriptions(scenario, characterDescriptionGenerator)
            assetManager.PopulateMissingCharacterProfile(scenario, characterPortraitGenerator)
            assetManager.PopulateMissingCharacterIcons(scenario, characterIconGenerator)
            assetManager.PopulateMissingCharacterChibis(scenario, characterChibiGenerator)

        populateMissingArtwork_button = st.button(label="Populate all missing artwork")
        if populateMissingArtwork_button:
            assetManager.CreateScenarioBackground(userId, scenario, backgroundGenerator)
            assetManager.PopulateMissingBuildingExteriors(scenario, buildingExteriorGenerator)
            assetManager.PopulateMissingBuildingInteriors(scenario, buildingInteriorGenerator)
            await assetManager.PopulateMissingCharacterDescriptions(scenario, characterDescriptionGenerator)
            assetManager.PopulateMissingCharacterProfile(scenario, characterPortraitGenerator)
            assetManager.PopulateMissingCharacterIcons(scenario, characterIconGenerator)
            assetManager.PopulateMissingCharacterChibis(scenario, characterChibiGenerator)

        redoCharacterImagery = st.button(label="Just redo all the characters")
        if redoCharacterImagery:
            for agent in scenario.GetAgents():
                #get a character description
                description = None
                try:
                    description = AgentDescriptionModel.objects.get(agentId=agent._id)
                except:
                    pass
                if description is None:
                    description = await characterDescriptionGenerator.DescribeCharacter(agent)
                    description.agentId = agent._id
                    AgentDescriptionModel.objects.insert(description)

                #redo the portrait
                description.portraitFilename = characterPortraitGenerator.CreatePortrait(agent, scenario, description)

                #redo the icon
                description.iconFilename, description.resizedIconFilename = characterIconGenerator.CreateIcon(agent, scenario, description)

                #redo the head icon
                description.chibiFilename, description.resizedChibiFilename = characterChibiGenerator.CreateChibi(agent, scenario, description)
                description.save()

    databaseContainer = st.container()
    with databaseContainer:
        writeAgents_button = st.button(label="Write agents to DB")
        if writeAgents_button:
            simulationRepository.SaveAgents(scenario)

        writeItems_button = st.button(label="Write items to DB")
        if writeItems_button:
            simulationRepository.SaveItems(scenario)

        goOutside_button = st.button(label="Everybody go outside")
        if goOutside_button:
            agents = scenario.GetAgents()
            for agent in agents:
                AgentRepository.CreateOrUpdate(agent, homeScenarioId=scenario._id)

        dropItems_button = st.button(label="Drop everything")
        if dropItems_button:
            agents = scenario.GetAgents()
            for agent in agents:
                itemManager.DropItem(scenario, agent, None, "There was an emergency.")

        upload_button = st.button(label="Upload to s3")
        if upload_button:
            #upload_file("bg2.png", "pixelvalley", "bg2.png")
            assetManager.UploadToS3(scenario)

    #output the user's prompt
    st.write(scenario)
    if scenario.imageFilename:
        st.image(f'{cloudFrontUri}{scenario.imageFilename}')

    st.subheader(f"Villagers in {scenario.name}:")
    for agent in scenario.GetAgents():
        try:
            description = AgentDescriptionModel.objects.get(agentId=agent._id)
        except:
            description = None
        
        st.write(agent)
        if agent.currentItem:
            st.write(f"{agent.name} is holding the {agent.currentItem.NameWithStatus()}")
        if agent.usingItem:
            st.write(f"{agent.name} is using the {agent.usingItem.NameWithStatus()}")
        if description is not None and description.portraitFilename:
            st.image(f'{cloudFrontUri}{description.portraitFilename}')
        if description is not None and description.resizedIconFilename:
            st.image(f'{cloudFrontUri}{description.resizedIconFilename}')
        if description is not None and description.resizedChibiFilename:
            st.image(f'{cloudFrontUri}{description.resizedChibiFilename}')

    st.subheader(f"Villagers that are standing outside:")
    if scenario.agents is not None:
        for agent in scenario.agents:
            st.write(agent.name)

    for location in scenario.locations:
        writeLocation(location)

def writeLocation(location, level = 0):
    #write the location
    st.header(f"{level}: {location}")
    if location.imageFilename:
        st.image(f'{cloudFrontUri}{location.imageFilename}')
    if location.imageInteriorFilename:
        st.image(f'{cloudFrontUri}{location.imageInteriorFilename}')

    #write all the items
    st.subheader(f"Items in {location.name}:")
    if location.items is not None:
        for item in location.items:
            st.write(item)
            if item.stateMachine is not None:
                st.write(item.stateMachine)

    #write all the villagers
    if location.agents is not None:
        st.subheader(f"Villagers in {location.name}:")
        for agent in location.agents:
            st.write(agent.name)

    if location.locations:
        level = level + 1
        st.subheader(f"Child locations of {location.name}:")
        for child in location.locations:
            writeLocation(child, level)
