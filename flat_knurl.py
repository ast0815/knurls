# -*- coding: utf-8 -*-
import adsk.core, adsk.fusion, adsk.cam, traceback
debug = True
handlers = []

def add_to_button(button):
    creation_handler = FlatKnurlCommandCreatedEventHandler()
    button.commandCreated.add(creation_handler)
    handlers.append(creation_handler)

# Event handler for the commandCreated event.
class FlatKnurlCommandCreatedEventHandler(adsk.core.CommandCreatedEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        eventArgs = adsk.core.CommandCreatedEventArgs.cast(args)
        cmd = eventArgs.command

        # Connect to the execute event.
        on_execute = FlatKnurlCommandExecuteHandler()
        cmd.execute.add(on_execute)
        handlers.append(on_execute)

# Event handler for the execute event.
class FlatKnurlCommandExecuteHandler(adsk.core.CommandEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        event_args = adsk.core.CommandEventArgs.cast(args)

        # Code to react to the event.
        app = adsk.core.Application.get()
        ui  = app.userInterface
        if debug:
            ui.messageBox('In command execute event handler.')
