# -*- coding: utf-8 -*-
#Author-Lukas Koch
#Description-Add knurls to flat surfaces.

import adsk.core, adsk.fusion, adsk.cam, traceback
from .flat_knurl import add_to_button as flat_knurl_button

debug = False

def run(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui  = app.userInterface
        if debug:
            ui.messageBox('Run addin')
        
        # Get the CommandDefinitions collection.
        cmd_defs = ui.commandDefinitions
        
        # Create a button command definition.
        button = cmd_defs.addButtonDefinition('KnurlButtonId', 
                                              'Knurl button', 
                                              'Knurl button tooltip',
                                              './resources/command')
        
        # Connect to the command.
        flat_knurl_button(button)
        
        # Get the ADD-INS panel in the model workspace. 
        addins_panel = ui.allToolbarPanels.itemById('SolidScriptsAddinsPanel')
        # Add the button to the bottom of the panel.
        addins_panel.controls.addCommand(button)
    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

def stop(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface
        if debug:
            ui.messageBox('Stop addin')
        
        # Clean up the UI.
        cmd_def = ui.commandDefinitions.itemById('KnurlButtonId')
        if cmd_def:
            cmd_def.deleteMe()
            
        addins_panel = ui.allToolbarPanels.itemById('SolidScriptsAddinsPanel')
        cntrl = addins_panel.controls.itemById('KnurlButtonId')
        if cntrl:
            cntrl.deleteMe()
    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))	