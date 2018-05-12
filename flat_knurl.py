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
        ui = None
        try:
            app = adsk.core.Application.get()
            ui  = app.userInterface

            event_args = adsk.core.CommandCreatedEventArgs.cast(args)
            cmd = event_args.command

            # Add a inputs for the command
            inputs = cmd.commandInputs

            # A flat face
            face = inputs.addSelectionInput('face', "Face", "Flat surface that will be knurled")
            face.addSelectionFilter('PlanarFaces')
            face.setSelectionLimits(1)

            # Shape of the knurls
            inputs.addValueInput('depth', 'Depth', 'mm', adsk.core.ValueInput.createByString('1 mm'))
            inputs.addValueInput('width', 'Width', 'mm', adsk.core.ValueInput.createByString('2 mm'))
            inputs.addValueInput('angle', 'Angle', 'deg', adsk.core.ValueInput.createByString('30 deg'))

            # Connect to the execute event.
            on_execute = FlatKnurlCommandExecuteHandler()
            cmd.execute.add(on_execute)
            handlers.append(on_execute)
        except:
            if ui:
                ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

# Event handler for the execute event.
class FlatKnurlCommandExecuteHandler(adsk.core.CommandEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        ui = None
        try:
            app = adsk.core.Application.get()
            ui  = app.userInterface
            if debug:
                ui.messageBox('In flat knurl command execute event handler.')

            # Code to react to the event.
            event_args = adsk.core.CommandEventArgs.cast(args)

            # Get the values from the command inputs.
            inputs = event_args.command.commandInputs
            width = inputs.itemById('width').value
            depth = inputs.itemById('depth').value
            angle = inputs.itemById('angle').value
            face = inputs.itemById('face').selection(0).entity

            if debug:
                ui.messageBox('%f'%(angle,))

            # Get extrude features
            product = app.activeProduct
            design = adsk.fusion.Design.cast(product)
            rootComp = design.rootComponent
            extrudes = rootComp.features.extrudeFeatures

            # Create the envelope
            extrusion_input = extrudes.createInput(face, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
            extrusion_distance = adsk.fusion.DistanceExtentDefinition.create(
                    adsk.core.ValueInput.createByReal(depth),
                    )
            extrusion_input.setOneSideExtent(extrusion_distance,
                    adsk.fusion.ExtentDirections.PositiveExtentDirection,
                    adsk.core.ValueInput.createByReal(-3.14159/2. + angle),
                    )
            envelope = extrudes.add(extrusion_input)

        except:
            if ui:
                ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
