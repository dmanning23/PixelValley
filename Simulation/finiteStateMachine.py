from py_linq import Enumerable

class StateTransition:
    def __init__(self, startState, action, targetState):
        self.startState = startState
        self.action = action
        self.targetState = targetState

    def __str__(self) -> str:
        return f"start: {self.startState}, action: {self.action}, end: {self.targetState}"

class FiniteStateMachine:

    def __init__(self, states, initialState, actions, transitions):
        #Set all the parameters of the finite state machine
        self.states = states
        self.initialState = initialState #TODO: error check the initial state!
        self.actions = actions
        transitionList = []
        for transition in transitions:
            #TODO: error check all transition items!
            transitionList.append(StateTransition(transition["startState"],
                                    transition["action"],
                                    transition["targetState"]))
            
        #Convert the transitions into an enumerable
        self.transitions = Enumerable(transitionList)

        #Set the current and previous states of the finite state machine
        self.previousState = self.initialState
        self.currentState = self.initialState

    def sendMessage(self, message):
        #Find a state transition that matched the current state and the action
        transition = self.transitions.first_or_default(lambda x: x.startState == self.currentState and x.action == message)
        if transition is not None:
            #does the state change?
            if self.currentState is not transition.targetState:
                #set the previous state
                self.previousState = self.currentState

                #set the current state
                self.currentState = transition.targetState

                #return the result
                return transition.output

    def __str__(self) -> str:
        result = f"""Current state: {self.currentState}\n
Previous state: {self.currentState}\n
Possible states: {self.states}\n
All available actions: {self.actions}\n
Transitions:\n\n"""
        for transition in self.transitions:
            result = result + f"{transition}\n\n"

        return result