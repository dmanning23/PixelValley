from Simulation.finiteStateMachine import FiniteStateMachine

class Item:
    """
    An item in the simulation that can be interacted with

    Attributes:
    name: string
        The name of the thing
    description: string
        A short description of the thing
    state: string
        A finite state machine for this item
    """
    def __init__(self, 
                 name, 
                 description, 
                 canInteract = False,
                 canBePickedUp = False,
                 stateMachine = None):
        self.name = name
        self.description = description
        self.canInteract = canInteract
        self.canBePickedUp = canBePickedUp
        self.stateMachine = stateMachine

    def Describe(self):
        description = f"""{self.name}\n
{self.description}\n
It is {"interactive" if self.canInteract else "non-interactive"}\n
It {"can" if self.canBePickedUp else "can not"} be picked up\n"""
        
        if self.stateMachine is not None:
            description = description + f"\n{self.stateMachine.Describe()}"

        return description