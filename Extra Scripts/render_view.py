# This script is for previewing the scene
# This is based on the original script which does not randomize the sun angle, and has broken PBR

import bpy
import sys
import os

source_folder = sys.argv[4]

# Process only the first folder
first_folder = next((f for f in os.listdir(source_folder) if os.path.isdir(os.path.join(source_folder, f))), None)

if first_folder:
    folder_path = os.path.join(source_folder, first_folder)
    
    bpy.ops.object.select_all(action='DESELECT')
    bpy.ops.object.select_by_type(type='MESH')
    bpy.ops.object.delete()

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

    for tex_type, suffix in texture_types.items():
        filename = first_folder + suffix
        image_path = os.path.join(folder_path, filename)
        if os.path.exists(image_path):
            tex_image = nodes.new('ShaderNodeTexImage')
            tex_image.image = bpy.data.images.load(image_path)
            tex_image.location = -400, 200 * list(texture_types.keys()).index(tex_type)

            if tex_type == "Base Color":
                material.node_tree.links.new(tex_image.outputs['Color'], shader.inputs['Base Color'])
            elif tex_type == "Normal":
                normal_map = nodes.new('ShaderNodeNormalMap')
                normal_map.location = -200, 200
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

    bpy.ops.mesh.primitive_plane_add(size=2, location=(0, 0, 0))
    plane = bpy.context.object
    plane.data.materials.append(material)

    bpy.ops.object.camera_add(location=(0, 0, 1))
    camera = bpy.context.object
    camera.data.type = 'ORTHO'
    camera.data.ortho_scale = 2.0
    bpy.context.scene.camera = camera

    # Remove the sun light
    bpy.ops.object.select_all(action='DESELECT')
    bpy.ops.object.select_by_type(type='LIGHT')
    bpy.ops.object.delete()

    # Add a new area light as a fill light
    bpy.ops.object.light_add(type='AREA', radius=5, location=(0, 0, 5))
    fill_light = bpy.context.object.data
    fill_light.energy = 250  # Increase this value to make the light brighter
    fill_light.size = 10  # Adjust the size to cover the entire plane

    bpy.context.scene.cycles.device = 'GPU'

    prefs = bpy.context.preferences
    cprefs = prefs.addons['cycles'].preferences
    cprefs.get_devices()
    cprefs.compute_device_type = 'OPTIX'

    for device in cprefs.devices:
        device.use = True

    bpy.context.scene.render.engine = 'CYCLES'
    bpy.context.scene.render.resolution_x = 2048
    bpy.context.scene.render.resolution_y = 2048

    print(f"Scene set up for {folder_path}. Open Blender to tweak the settings.")
