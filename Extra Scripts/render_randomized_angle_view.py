# This script is for previewing the scene
# This is based on the randomized sun angle script, which has fixed PBR (hopefully)

import bpy
import sys
import os
import random
import numpy as np

# Get the source folder path
source_folder = r"C:\Users\Kim\Projects\Render\test"  # Replace with your actual source folder path

# Iterate over folders in the source folder
for folder_name in os.listdir(source_folder):
    folder_path = os.path.join(source_folder, folder_name)
    if os.path.isdir(folder_path):
        # Clear the scene
        bpy.ops.object.select_all(action='DESELECT')
        bpy.ops.object.select_by_type(type='MESH')
        bpy.ops.object.delete()

        # Create a new material
        material = bpy.data.materials.new(name="PBR_Material")
        material.use_nodes = True
        nodes = material.node_tree.nodes
        nodes.clear()

        shader = nodes.new(type='ShaderNodeBsdfPrincipled')
        shader.location = 0, 0

        output = nodes.new(type='ShaderNodeOutputMaterial')
        output.location = 400, 0

        material.node_tree.links.new(shader.outputs['BSDF'], output.inputs['Surface'])

        texture_types = {
            "Base Color": "_diffuse.png",
            "Normal": "_normal.png",
            "Roughness": "_roughness.png",
            "Metallic": "_metalness.png",
            "Height": "_height.png"
        }

        # Load the first texture set found
        for tex_type, suffix in texture_types.items():
            filename = folder_name + suffix
            image_path = os.path.join(folder_path, filename)
            if os.path.exists(image_path):
                tex_image = nodes.new('ShaderNodeTexImage')
                tex_image.image = bpy.data.images.load(image_path)
                tex_image.location = -400, 0

                if tex_type == "Base Color":
                    material.node_tree.links.new(tex_image.outputs['Color'], shader.inputs['Base Color'])
                elif tex_type == "Normal":
                    normal_map = nodes.new('ShaderNodeNormalMap')
                    normal_map.location = -200, 0
                    material.node_tree.links.new(tex_image.outputs['Color'], normal_map.inputs['Color'])

                    # Control the strength of the normal map
                    normal_strength = 0.5  # Set your desired strength here
                    normal_map.inputs['Strength'].default_value = normal_strength

                    material.node_tree.links.new(normal_map.outputs['Normal'], shader.inputs['Normal'])
                elif tex_type == "Roughness":
                    material.node_tree.links.new(tex_image.outputs['Color'], shader.inputs['Roughness'])
                elif tex_type == "Metallic":
                    material.node_tree.links.new(tex_image.outputs['Color'], shader.inputs['Metallic'])
                elif tex_type == "Height":
                    displacement = nodes.new('ShaderNodeDisplacement')
                    displacement.inputs['Scale'].default_value = 0.1  # Adjust the scale value as needed
                    displacement.inputs['Midlevel'].default_value = 0.5  # Adjust the midlevel value as needed
                    displacement.location = -200, -200
                    material.node_tree.links.new(tex_image.outputs['Color'], displacement.inputs['Height'])
                    material.node_tree.links.new(displacement.outputs['Displacement'], output.inputs['Displacement'])

                # Exit the loop after loading the first texture set
                break

        # Add a plane and assign the material
        bpy.ops.mesh.primitive_plane_add(size=2, location=(0, 0, 0))
        plane = bpy.context.object
        plane.data.materials.append(material)

        # Add a camera
        bpy.ops.object.camera_add(location=(0, 0, 1))
        camera = bpy.context.object
        camera.data.type = 'ORTHO'
        camera.data.ortho_scale = 2.0
        bpy.context.scene.camera = camera

        # Remove the default sun light
        bpy.ops.object.select_all(action='DESELECT')
        bpy.ops.object.select_by_type(type='LIGHT')
        bpy.ops.object.delete()

        # Add a new area light as an ambient fill light
        bpy.ops.object.light_add(type='AREA', radius=5, location=(0, 0, 5))
        fill_light = bpy.context.object.data
        fill_light.energy = 5  # Very weak energy for ambient fill light
        fill_light.size = 20  # Large size to cover the entire plane

        # Add a new sun light at a randomized angle within 130 degrees of the top of the plane
        theta = random.uniform(0, 130) * (np.pi / 180)  # Convert degrees to radians
        phi = random.uniform(0, 360) * (np.pi / 180)
        sun_x = 5 * np.sin(theta) * np.cos(phi)
        sun_y = 5 * np.sin(theta) * np.sin(phi)
        sun_z = random.uniform(2, 5)  # Randomize the z-coordinate within the range of 2 to 5
        bpy.ops.object.light_add(type='SUN', location=(sun_x, sun_y, sun_z))
        sun = bpy.context.object
        sun_light = sun.data
        sun_light.energy = 2  # Set the energy of the sun light

        # Point the sun light towards the center of the plane
        sun.rotation_euler = (theta, phi, 0)
        sun.data.node_tree.nodes["Emission"].inputs["Strength"].default_value = 2


        # Enable GPU rendering and denoising
        bpy.context.scene.cycles.device = 'GPU'
        prefs = bpy.context.preferences
        cprefs = prefs.addons['cycles'].preferences
        cprefs.get_devices()
        cprefs.compute_device_type = 'OPTIX'
        bpy.context.scene.view_layers[0].cycles.use_denoising = True
        bpy.context.scene.view_layers[0].cycles.denoising_type = 'OPTIX'
        for device in cprefs.devices:
            device.use = True

        # Set the rendering engine and resolution
        bpy.context.scene.render.engine = 'CYCLES'
        bpy.context.scene.render.resolution_x = 2048
        bpy.context.scene.render.resolution_y = 2048

        # Exit the loop after loading and setting up the first texture set
        break