import bpy
import sys
import os
import random
import numpy as np
import mathutils

source_folder = sys.argv[5]

def set_adaptive_subsurf(obj):
    # First subdivision modifier
    subsurf1 = obj.modifiers.new(name="Subdivision1", type='SUBSURF')
    subsurf1.subdivision_type = 'SIMPLE'
    subsurf1.levels = 6
    subsurf1.render_levels = 6

    # Second subdivision modifier
    subsurf2 = obj.modifiers.new(name="Subdivision2", type='SUBSURF')
    subsurf2.subdivision_type = 'SIMPLE'
    subsurf2.levels = 4
    subsurf2.render_levels = 4

def initialize_scene():
    # Remove all existing objects
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()

    # Initialize camera
    bpy.ops.object.camera_add(location=(0, 0, 1))
    camera = bpy.context.object
    camera.data.type = 'ORTHO'
    camera.data.ortho_scale = 2.0
    bpy.context.scene.camera = camera

    # Initialize fill light (area light)
    bpy.ops.object.light_add(type='AREA', radius=5, location=(0, 0, 5))
    fill_light = bpy.context.object.data
    fill_light.energy = 5  # Very weak energy for ambient fill light
    fill_light.size = 20 

    # Add randomized sun light
    min_sun_z = 3
    sun_distance = random.uniform(3, 5)  
    max_theta = np.arccos(min_sun_z / sun_distance)
    sun_theta = random.uniform(0, max_theta) 
    sun_phi = random.uniform(0, 360) * (np.pi / 180)

    sun_x = sun_distance * np.sin(sun_theta) * np.cos(sun_phi)
    sun_y = sun_distance * np.sin(sun_theta) * np.sin(sun_phi)
    sun_z = sun_distance * np.cos(sun_theta)

    bpy.ops.object.light_add(type='SUN', location=(sun_x, sun_y, sun_z))
    sun_light = bpy.context.object.data
    sun_light.energy = 2 

    direction = mathutils.Vector((-sun_x, -sun_y, -sun_z))
    rot_quat = direction.to_track_quat('-Z', 'Y')
    bpy.context.object.rotation_euler = rot_quat.to_euler()

    # Create plane
    bpy.ops.mesh.primitive_plane_add(size=2, location=(0, 0, 0))
    plane = bpy.context.object
    set_adaptive_subsurf(plane)

    # Setup OptiX
    prefs = bpy.context.preferences
    cprefs = prefs.addons['cycles'].preferences
    cprefs.get_devices()
    cprefs.compute_device_type = 'OPTIX'
    bpy.context.scene.cycles.use_denoising = True
    bpy.context.scene.cycles.denoiser = 'OPTIX'

    for device in cprefs.devices:
        device.use = True

    bpy.context.scene.render.resolution_x = 2048
    bpy.context.scene.render.resolution_y = 2048

    # Set render engine to Cycles
    bpy.context.scene.render.engine = 'CYCLES'
    bpy.context.scene.cycles.device = 'GPU'
    bpy.context.scene.cycles.progressive = 'EXPERIMENTAL'

    return plane, camera, sun_light, fill_light

def create_material(folder_name, folder_path):
    material = bpy.data.materials.new(name=f"PBR_Material_{folder_name}")
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
        "Normal": "_normal_ogl.png",
        "Roughness": "_roughness.png",
        "Metallic": "_metalness.png",
        "Height": "_height.png"
    }

    for tex_type, suffix in texture_types.items():
        filename = folder_name + suffix
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
                tex_image.image.colorspace_settings.name = 'Non-Color'

                # Control the strength of the normal map
                normal_strength = 0.75
                normal_map.inputs['Strength'].default_value = normal_strength

                material.node_tree.links.new(normal_map.outputs['Normal'], shader.inputs['Normal'])
                
            elif tex_type == "Roughness":
                material.node_tree.links.new(tex_image.outputs['Color'], shader.inputs['Roughness'])
                tex_image.image.colorspace_settings.name = 'Non-Color'
                
            elif tex_type == "Metallic":
                material.node_tree.links.new(tex_image.outputs['Color'], shader.inputs['Metallic'])
                tex_image.image.colorspace_settings.name = 'Non-Color'
                
            elif tex_type == "Height":
                tex_image.image.colorspace_settings.name = 'Non-Color'
                displacement = nodes.new('ShaderNodeDisplacement')
                material.displacement_method = 'BOTH'
                displacement.inputs['Midlevel'].default_value = 0.0 
                displacement.inputs['Scale'].default_value = 0.05
                displacement.location = -200, -200
                material.node_tree.links.new(tex_image.outputs['Color'], displacement.inputs['Height'])
                material.node_tree.links.new(displacement.outputs['Displacement'], output.inputs['Displacement'])

    return material

# Initialize scene and get the plane object
plane, camera, sun_light, fill_light = initialize_scene()

for folder_name in os.listdir(source_folder):
    folder_path = os.path.join(source_folder, folder_name)
    if os.path.isdir(folder_path):
        # Create material for this texture set
        material = create_material(folder_name, folder_path)

        # Assign material to the plane
        if plane.data.materials:
            plane.data.materials[0] = material
        else:
            plane.data.materials.append(material)

        # Set render path and render
        render_path = os.path.join(folder_path, f"{folder_name}_render_fixed_angle_v2.png")
        bpy.context.scene.render.filepath = render_path

        bpy.ops.render.render(write_still=True)
        print(f"Rendered {render_path}")

        # Clean up: remove the material after rendering
        bpy.data.materials.remove(material)

# Clean up: remove the plane after all renders are complete
bpy.data.objects.remove(plane, do_unlink=True)