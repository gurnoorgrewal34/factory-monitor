class GroupProcessor:

    def __init__(self, memory, behaviour):

        self.memory = memory
        self.behaviour = behaviour

    ##################################################

    def process(self):

        alerts = self.behaviour.process_group(

            self.memory.all_people()

        )

        return alerts