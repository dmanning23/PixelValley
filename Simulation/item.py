
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
                 stateMachine = None,
                 _id = None,
                 status = None,
                 emoji = None):
        if _id is not None:
            self._id = _id
        self.name = name
        self.description = description
        self.canInteract = canInteract
        self.canBePickedUp = canBePickedUp
        self.stateMachine = stateMachine
        self.status = status
        self.emoji = emoji

    def __str__(self) -> str:
        return f"""{self.NameWithStatus()}\n
{self.description}\n
It is {"interactive" if self.canInteract else "non-interactive"}\n
It {"can" if self.canBePickedUp else "can not"} be picked up\n"""
    
    def NameWithStatus(self):
        if self.status:
            return f"{self.name}, which is {self.status}"
        else:
            return f"{self.name}"