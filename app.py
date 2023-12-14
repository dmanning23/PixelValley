import os
import streamlit as st
from openai import OpenAI
from keys import openAIapikey
from keys import mongoUri
import json
from random import *
import sys
from mongoengine import *
from Generators.scenarioGenerator import ScenarioGenerator
from Generators.locationGenerator import LocationGenerator
from Generators.itemGenerator import ItemGenerator
from Generators.agentGenerator import AgentGenerator
from Simulation.location import Location
from Simulation.item import Item
from Simulation.scenario import Scenario
from Generators.finiteStateMachineGenerator import FiniteStateMachineGenerator
from Repository.scenarioRepository import ScenarioRepository
from Repository.locationRepository import LocationRepository
from Repository.agentRepository import AgentRepository
from Repository.itemRepository import ItemRepository
from Repository.userAccessRepository import UserAccessRepository

def main():

    #Set up the api key for OpenAI
    #os.environ["OPENAI_API_KEY"] = st.secrets["OPENAI_API_KEY"]
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
        scenario.agents = AgentRepository.GetAgents(currentScenarioId=scenario._id)
        for location in scenario.locations:
            AgentRepository.FetchLocation(location)

    #store the scenario
    st.session_state["scenario"] = scenario
    st.rerun()

def createScenario(userId, scenarioDescription):
    with st.spinner("Creating scenario..."):
        #expand the setting
        settingGen = ScenarioGenerator()
        scenario = settingGen.Generate(scenarioDescription)

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
                #items = items + itemGen.PopulateLocations(location)
                pass

    with st.spinner("Reticulating splines..."):
        for item in items:
            #itemGen.GenerateFiniteStateMachine(item)
            pass

    #create all the villagers
    with st.spinner("Creating villagers..."):
        agentGen = AgentGenerator()
        scenario.agents = agentGen.GenerateCharacters(scenario)
        #place each villager somewhere
        for agent in scenario.agents:
            #get a random location
            locationIndex = randint(0, len(scenario.locations))
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
        for agent in scenario.agents:
            AgentRepository.CreateOrUpdate(agent, homeScenarioId=scenario._id)
        for location in scenario.locations:
            AgentRepository.CreateOrUpdateFromLocation(location, homeScenarioId=scenario._id)

    #store the scenario
    st.session_state["scenario"] = scenario
    st.rerun()

def displayScenario(scenario):

    #output the user's prompt
    st.markdown(scenario.name)
    st.markdown(scenario.description)

    if scenario.agents is not None:
        st.subheader(f"Villagers in {scenario.name}:")
        for agent in scenario.agents:
            st.write(agent)

    for location in scenario.locations:
        writeLocation(location)

def writeLocation(location, level = 0):
    #write the location
    st.header(location)

    #write all the items
    st.subheader(f"Items in {location.name}:")
    if location.items is not None:
        for item in location.items:
            st.write(item)

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
