# -*- coding: utf-8 -*-
import adsk.core, adsk.fusion, adsk.cam, traceback
debug = False
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
            face.addSelectionFilter('Profiles')
            face.setSelectionLimits(1)

            # Shape of the knurls
            inputs.addValueInput('depth', 'Depth', 'mm', adsk.core.ValueInput.createByString('0.5 mm'))
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

            # Get extrude features
            product = app.activeProduct
            design = adsk.fusion.Design.cast(product)
            rootComp = design.rootComponent
            extrudes = rootComp.features.extrudeFeatures

            # Add sketch
            sketches = rootComp.sketches
            face_type = 'face'
            try:
                sketch = sketches.add(face)
            except RuntimeError:
                # We probably have a profile instead of a face
                face_type = 'profile'
                sketch = face.parentSketch

            # Get minimum and maximum coordinates
            bounds = sketch.profiles.item(0).boundingBox
            x_min = bounds.minPoint.x
            y_min = bounds.minPoint.y
            x_max = bounds.maxPoint.x
            y_max = bounds.maxPoint.y

            # Calculate how to fill the area
            Dx = x_max - x_min
            Dy = y_max - y_min
            Nx = (Dx / width)
            Ny = (Dy / width)
            dx = -width*(1.-(Nx % 1))/2. # Offsets to make things symmetrical
            dy = -width*(1.-(Ny % 1))/2.
            Nx = int(Nx) + 2
            Ny = int(Ny) + 2

            if debug:
                ui.messageBox('%s %s %s'%(Dx, Nx, dx))

            # Draw single knurl base outside face bounds, so there is no overlap of profiles
            lines = sketch.sketchCurves.sketchLines;
            rectangle = lines.addTwoPointRectangle(adsk.core.Point3D.create(x_min-width+dx, y_min-width+dy, 0), adsk.core.Point3D.create(x_min+dx, y_min+dy, 0))
            # Find base of knurl within sketch profiles
            # Should be the one with the lowest minimum coordinates
            base = sketch.profiles.item(0)
            for i in range(1, sketch.profiles.count):
                alt_base = sketch.profiles.item(i)
                if alt_base.boundingBox.minPoint.x < base.boundingBox.minPoint.x:
                    base = alt_base

            # Extrude knurl
            extrusion_input = extrudes.createInput(base, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
            extrusion_distance = adsk.fusion.DistanceExtentDefinition.create(
                    adsk.core.ValueInput.createByReal(depth),
                    )
            extrusion_input.setOneSideExtent(extrusion_distance,
                    adsk.fusion.ExtentDirections.PositiveExtentDirection,
                    adsk.core.ValueInput.createByReal(-3.14159/2. + angle),
                    )
            knurl = extrudes.add(extrusion_input).bodies.item(0) # Body created by extrude

            # Create input entities for rectangular pattern
            input_entities = adsk.core.ObjectCollection.create()
            input_entities.add(knurl)

            # Get x and y axes for rectangular pattern
            xAxis = rectangle.item(0)
            yAxis = rectangle.item(1)

            # Quantity and distance
            quantityOne = adsk.core.ValueInput.createByString("%d"%(Nx,))
            distanceOne = adsk.core.ValueInput.createByReal(-width) # Axis is in "wrong" direction
            quantityTwo = adsk.core.ValueInput.createByString("%d"%(Ny,))
            distanceTwo = adsk.core.ValueInput.createByReal(width)

            # Create the input for rectangular pattern
            rectangularPatterns = rootComp.features.rectangularPatternFeatures
            rectangularPatternInput = rectangularPatterns.createInput(input_entities, xAxis, quantityOne, distanceOne, adsk.fusion.PatternDistanceType.SpacingPatternDistanceType)

            # Set the data for second direction
            rectangularPatternInput.setDirectionTwo(yAxis, quantityTwo, distanceTwo)

            # Create the rectangular pattern
            rectangular_feature = rectangularPatterns.add(rectangularPatternInput)

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

            # Create input entities for combine
            input_entities = adsk.core.ObjectCollection.create()
            input_entities.add(knurl)
            for i in range(rectangular_feature.bodies.count):
                input_entities.add(rectangular_feature.bodies.item(i))

            # Get intersection of envelope and pattern
            combines = rootComp.features.combineFeatures
            combine_input = combines.createInput(envelope.bodies.item(0), input_entities)
            combine_input.operation = adsk.fusion.FeatureOperations.IntersectFeatureOperation
            knurls = combines.add(combine_input)

            # Create input entities for combine
            input_entities = adsk.core.ObjectCollection.create()
            for i in range(knurls.bodies.count):
                input_entities.add(knurls.bodies.item(i))

            # Union of intersection and original body
            if face_type == 'profile':
                face = sketch.referencePlane
            try:
                base_body = face.body
            except AttributeError:
                pass # Sketch is not on a body
            else:
                combine_input = combines.createInput(base_body, input_entities)
                combine_input.operation = adsk.fusion.FeatureOperations.JoinFeatureOperation
                final = combines.add(combine_input)

        except:
            if ui:
                ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
