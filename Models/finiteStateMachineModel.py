from Simulation.finiteStateMachine import *
from mongoengine import *
from py_linq import *

class StateTransitionModel(EmbeddedDocument):
    startState = StringField()
    action = StringField()
    targetState = StringField()

    def Set(self, transition):
        self.startState = transition.startState
        self.action = transition.action
        self.targetState = transition.targetState

class FiniteStateMachineModel(EmbeddedDocument):
    states = ListField()
    initialState = StringField()
    actions = ListField()
    transitionList = ListField(EmbeddedDocumentField(StateTransitionModel))
    previousState = StringField()
    currentState = StringField()

    def Set(self, finiteStateMachine):
        self.states = finiteStateMachine.states
        self.initialState = finiteStateMachine.initialState
        self.actions = finiteStateMachine.actions
        self.previousState = finiteStateMachine.previousState
        self.currentState = finiteStateMachine.currentState
        for transition in finiteStateMachine.transitions:
            model = StateTransitionModel()
            model.Set(transition)
            self.transitionList.append(model)

    def Hydrate(self):
        enums = Enumerable(self.transitionList)
        return FiniteStateMachine(self.states,
                                  self.initialState,
                                  self.actions,
                                  enums.select(lambda x: {
                                      "startState": x.startState,
                                      "action": x.action,
                                      "targetState": x.targetState}))

