import os
import streamlit as st
from keys import openAIapikey
from keys import mongoUri
from random import *
from mongoengine import *
from py_linq import *

from Simulation.timeStream import TimeStream

from Generators.scenarioGenerator import ScenarioGenerator
from Generators.locationGenerator import LocationGenerator
from Generators.itemGenerator import ItemGenerator
from Generators.agentGenerator import AgentGenerator
from Generators.goalsGenerator import GoalsGenerator
from Generators.plannedActivityGenerator import PlannedActivityGenerator

from Repository.scenarioRepository import ScenarioRepository
from Repository.locationRepository import LocationRepository
from Repository.agentRepository import AgentRepository
from Repository.itemRepository import ItemRepository
from Repository.goalsRepository import GoalsRepository

from Memory.memoryRepository import MemoryRepository
from Memory.observationStream import ObservationStream
from Memory.retrievalStream import RetrievalStream
from Memory.reflectionStream import ReflectionStream
from Memory.goalsStream import GoalsStream
from Memory.plannedActivityStream import PlannedActivityStream

from Interactions.interactionGenerator import InteractionGenerator
from Interactions.interactionStream import InteractionStream
from Interactions.actionGenerator import ActionGenerator
from Interactions.conversationGenerator import ConversationGenerator

def main():

    #Set up the api key for OpenAI
    os.environ["OPENAI_API_KEY"] = openAIapikey

     #spin up mongoDB
    connect(host=mongoUri, db="pixelValley") #connect for mongoengine

    initializeScenario()

def clearSession():
    st.session_state["scenario"]=None

def initializeScenario():
    userId = st.session_state["userId"]

    if "scenario" in st.session_state and st.session_state['scenario'] is not None:
        scenario = st.session_state["scenario"]
        displayScenario(userId, scenario)

    else:
        st.subheader("Select an existing scenario, or create a new one")

        #Get the user's scenarios
        userId = st.session_state["userId"]
        scenarios = ScenarioRepository.GetScenarios(userId)
        if scenarios:
            selectContainer = st.container()
            with selectContainer:
                with st.form(key="select scenario", clear_on_submit=True):
                    selectedScenario  = st.selectbox("Select an existing scenario:", scenarios)
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
                    createScenario(userId, user_input)

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
            items = ItemRepository.GetItems(characterId=agent._id)
            if items is not None and len(items) > 0:
                agent.currentItem = items[0]

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
            itemGen.GenerateFiniteStateMachine(item)
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
            

    with st.spinner("Saving scenario..."):
        #Store the scenario
        ScenarioRepository.CreateOrUpdate(userId, scenario)

    with st.spinner("Saving locations..."):
        for location in scenario.locations:
            LocationRepository.CreateOrUpdateLocations(location, scenario._id)

    with st.spinner("Saving items..."):
        for location in scenario.locations:
            ItemRepository.CreateOrUpdateFromLocation(location)

    #save all the villagers
    with st.spinner("Saving villagers..."):
        if scenario.agents is not None:
            for agent in scenario.agents:
                AgentRepository.CreateOrUpdate(agent, homeScenarioId=scenario._id)
        for location in scenario.locations:
            AgentRepository.CreateOrUpdateFromLocation(location, homeScenarioId=scenario._id)

    #store the scenario
    st.session_state["scenario"] = scenario
    st.rerun()

def displayScenario(userId, scenario):

    memRepo = MemoryRepository()
    obsStream = ObservationStream(memRepo)
    goalRepo = GoalsRepository()
    retrieval = RetrievalStream(memRepo)
    reflection = ReflectionStream(memRepo, retrieval)
    goalGen = GoalsGenerator()
    goalsStream = GoalsStream(memRepo, goalGen, goalRepo)
    activityGen = PlannedActivityGenerator()
    activityStream = PlannedActivityStream(memRepo, activityGen, goalRepo, retrieval)
    interactionGen = InteractionGenerator()
    itemRepo = ItemRepository()
    agentRepo = AgentRepository()
    actionGenerator = ActionGenerator()
    conversationGenerator = ConversationGenerator()
    iteractionStream = InteractionStream(activityStream, retrieval, interactionGen, itemRepo, memRepo, agentRepo, actionGenerator)
    timeStream = TimeStream()
    
    clear_button = st.button(label="Clear memory")
    if clear_button:
        memRepo.collection.delete_many({"time": { "$lt": 10 }})

    #increment the time for each agent
    time_button = st.button(label="Increment Time")
    if time_button:
        timeStream.IncrementTime(userId, scenario)

    createContainer = st.container()
    with createContainer:
        #Create some observational memories
        observe_button = st.button(label="Create Observations")
        if observe_button:
            #make some observations
            obsStream.CreateScenarioObservations(scenario)

        reflect_button = st.button(label="Create Reflections")
        if reflect_button:
            for agent in scenario.GetAgents():
                reflection.CreateReflections(agent)

        goals_button = st.button(label="Create Goals")
        if goals_button:
            for agent in scenario.GetAgents():
                goalsStream.CreateGoals(agent, scenario)

        plans_button = st.button(label="Create Daily Planned Activities")
        if plans_button:
            for agent in scenario.GetAgents():
                activityStream.CreatePlannedActivities(agent, scenario)

        change_location_button = st.button(label="Change Agent Locations?")
        if change_location_button:
            for agent in scenario.GetAgents():
                iteractionStream.ChangeLocation(agent, scenario)

        change_item_button = st.button(label="Swap Items?")
        if change_item_button:
            for agent in scenario.GetAgents():
                iteractionStream.SwapItems(agent, scenario)

        item_interaction_button = st.button(label="Use an item?")
        if item_interaction_button:
            for agent in scenario.GetAgents():
                iteractionStream.UseItem(agent, scenario)

        agent_status_button = st.button(label="Set Agent statuses")
        if agent_status_button:
            for agent in scenario.GetAgents():
                iteractionStream.SetAgentStatus(agent, scenario)

        action_button = st.button(label="Plan actions")
        if action_button:
            for agent in scenario.GetAgents():
                iteractionStream.PlanActions(agent, scenario)

        conversation_button = st.button(label="Have conversation")
        if conversation_button:
            #get the list of agents
            agents = scenario.GetAgents()
            agent1 = agents[0]
            agent2 = agents[1]

            #get the planned activity of each agent
            agent1PlannedActivity = activityStream.GetCurrentPlannedActivity(agent1, scenario.currentDateTime)
            agent2PlannedActivity = activityStream.GetCurrentPlannedActivity(agent1, scenario.currentDateTime)

            #get memories for each agent
            agent1Memories = retrieval.RetrieveMemories(agent1, f'What is {agent1.name}\'s relationship with {agent2.name}?')
            agent2Memories = retrieval.RetrieveMemories(agent2, f'What is {agent2.name}\'s relationship with {agent1.name}?')

            #create a conversation
            conversation = conversationGenerator.CreateConversation(scenario, agent1, agent2, agent1PlannedActivity, agent2PlannedActivity, agent1Memories, agent2Memories)

        conversation_button2 = st.button(label="Have conversation 2")
        if conversation_button2:
            #get the list of agents
            agents = scenario.GetAgents()
            conversationAgents = [ agents[0], agents[1] ]

            #get the planned activity of each agent
            plannedActivities = [
                activityStream.GetCurrentPlannedActivity(agents[0], scenario.currentDateTime),
                activityStream.GetCurrentPlannedActivity(agents[1], scenario.currentDateTime)
            ]

            #get memories for each agent
            memories = [
                retrieval.RetrieveMemories(agents[0], f'What is {agents[0].name}\'s relationship with {agents[1].name}?'),
                retrieval.RetrieveMemories(agents[1], f'What is {agents[1].name}\'s relationship with {agents[0].name}?')
            ]

            #create a conversation
            conversation = conversationGenerator.CreateConversation(scenario, conversationAgents, plannedActivities, memories)

        conversation_button3 = st.button(label="Have conversation 3")
        if conversation_button3:
            #get the list of agents
            agents = scenario.GetAgents()
            conversationAgents = [ agents[0], agents[1], agents[2] ]

            #get the planned activity of each agent
            plannedActivities = []
            for agent in conversationAgents:
                plannedActivities.append(activityStream.GetCurrentPlannedActivity(agent, scenario.currentDateTime))

            #get memories for each agent
            memories = []
            for i in range(len(conversationAgents)):
                agentMemories = []
                for j in range(len(conversationAgents)):
                    if i != j:
                        agentMemories.extend(retrieval.RetrieveMemories(agents[i], f'What is {agents[i].name}\'s relationship with {agents[j].name}?'))
                memories.append(agentMemories)

            #create a conversation
            conversation = conversationGenerator.CreateConversation(scenario, conversationAgents, plannedActivities, memories)

    #output the user's prompt
    st.write(scenario)

    st.subheader(f"Villagers in {scenario.name}:")
    for agent in scenario.GetAgents():
        st.write(agent)

    st.subheader(f"Villagers that are standing outside:")
    if scenario.agents is not None:
        for agent in scenario.agents:
            st.write(agent.name)

    for location in scenario.locations:
        writeLocation(location)

def writeLocation(location, level = 0):
    #write the location
    st.header(f"{level}: {location}")

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
