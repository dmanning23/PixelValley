import os
import streamlit as st
from keys import openAIapikey
from keys import mongoUri
from random import *
from mongoengine import *

from Generators.scenarioGenerator import ScenarioGenerator
from Generators.locationGenerator import LocationGenerator
from Generators.itemGenerator import ItemGenerator
from Generators.agentGenerator import AgentGenerator

from Repository.scenarioRepository import ScenarioRepository
from Repository.locationRepository import LocationRepository
from Repository.agentRepository import AgentRepository
from Repository.itemRepository import ItemRepository

from Memory.memoryRepository import MemoryRepository
from Memory.observationStream import ObservationStream
from Memory.retrievalStream import RetrievalStream
from Memory.reflectionStream import ReflectionStream

def main():

    #Set up the api key for OpenAI
    os.environ["OPENAI_API_KEY"] = openAIapikey

     #spin up mongoDB
    connect(host=mongoUri, db="pixelValley") #connect for mongoengine

    initializeScenario()

def clearSession():
    st.session_state["scenario"]=None

def initializeScenario():
    if "scenario" in st.session_state and st.session_state['scenario'] is not None:
        scenario = st.session_state["scenario"]
        displayScenario(scenario)

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

def displayScenario(scenario):

    #Create some observational memories
    observe_button = st.button(label="Create Observations")
    if observe_button:
        #create all the stuff we need to make observations
        #create the memory repository
        memRepo = MemoryRepository()

        #create the observation stream
        obsStream = ObservationStream(memRepo)

        #make some observations
        obsStream.CreateScenarioObservations(scenario)

    clear_button = st.button(label="Clear memory")
    if clear_button:
        memRepo = MemoryRepository()
        memRepo.collection.delete_many({"time": { "$lt": 10 }})

    #increment the time for each agent
    time_button = st.button(label="Increment Time")
    if time_button:
        for agent in scenario.GetAgents():
            agent.IncrementTime()
            AgentRepository.CreateOrUpdate(agent, homeScenarioId=scenario._id)

    reflect_button = st.button(label="Create Reflections")
    if reflect_button:
        for agent in scenario.GetAgents():
            memRepo = MemoryRepository()
            retrieval = RetrievalStream(memRepo)
            reflection = ReflectionStream(memRepo, retrieval)
            memories = reflection.CreateReflections(agent)

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
