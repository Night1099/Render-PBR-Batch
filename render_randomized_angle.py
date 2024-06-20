import bpy
import sys
import os
import random
import numpy as np
import mathutils

source_folder = sys.argv[5]


def set_adaptive_subsurf1(obj):
    subsurf = obj.modifiers.new("Subdivision", 'SUBSURF')
    subsurf.subdivision_type = 'SIMPLE'
    subsurf.levels = 6
    subsurf.render_levels = 6


def set_adaptive_subsurf2(obj):
    subsurf = obj.modifiers.new("Subdivision", 'SUBSURF')
    subsurf.subdivision_type = 'SIMPLE'
    subsurf.levels = 4
    subsurf.render_levels = 4


    # Other settings to mess with
    # subsurf.max_level = 4 
    # subsurf.quality = 3
    # subsurf.boundary_smooth = 'PRESERVE_CORNERS'

for folder_name in os.listdir(source_folder):
    folder_path = os.path.join(source_folder, folder_name)
    if os.path.isdir(folder_path):
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

                    # Control the strength of the normal map
                    normal_strength = 0.5  # Set your desired strength here
                    normal_map.inputs['Strength'].default_value = normal_strength

                    material.node_tree.links.new(normal_map.outputs['Normal'], shader.inputs['Normal'])
                elif tex_type == "Roughness":
                    material.node_tree.links.new(tex_image.outputs['Color'], shader.inputs['Roughness'])
                elif tex_type == "Metallic":
                    material.node_tree.links.new(tex_image.outputs['Color'], shader.inputs['Metallic'])
                elif tex_type == "Height":
                    tex_image.image.colorspace_settings.name = 'Non-Color'  # Load height map as non-color
                    displacement = nodes.new('ShaderNodeDisplacement')
                    displacement.inputs['Height'].default_value = 1.0  # Set to 'Displacement and Bump'
                    displacement.inputs['Midlevel'].default_value = 0.0  # Set midlevel to 0
                    displacement.inputs['Scale'].default_value = 0.05  # Set scale to 0.05
                    displacement.location = -200, -200
                    material.node_tree.links.new(tex_image.outputs['Color'], displacement.inputs['Height'])
                    material.node_tree.links.new(displacement.outputs['Displacement'], output.inputs['Displacement'])

        bpy.ops.mesh.primitive_plane_add(size=2, location=(0, 0, 0))
        plane = bpy.context.object
        plane.data.materials.append(material)
        plane.modifiers.new("Subdivision", 'SUBSURF')

        set_adaptive_subsurf1(plane)
        bpy.ops.object.modifier_apply(modifier="Subdivision")

        set_adaptive_subsurf2(plane)


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

        sun_distance = random.uniform(2, 5)  
        sun_theta = random.uniform(0, 90) * (np.pi / 180)
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

        bpy.context.scene.cycles.device = 'GPU'
        bpy.context.scene.render.engine = 'CYCLES'
        bpy.context.scene.cycles.progressive = 'EXPERIMENTAL'  # Set renderer to experimental

        prefs = bpy.context.preferences
        cprefs = prefs.addons['cycles'].preferences
        cprefs.get_devices()
        cprefs.compute_device_type = 'OPTIX'

        # Enable denoising and set to OptiX
        bpy.context.scene.view_layers[0].cycles.use_denoising = True
        bpy.context.scene.view_layers[0].cycles.denoising_type = 'OPTIX'

        # Disable Transparent Shadows
        bpy.context.scene.render.film_transparent = False

        for device in cprefs.devices:
            device.use = True

        bpy.context.scene.render.resolution_x = 2048
        bpy.context.scene.render.resolution_y = 2048
        render_path = os.path.join(folder_path, f"{folder_name}_render_random.png")
        bpy.context.scene.render.filepath = render_path

        bpy.ops.render.render(write_still=True)
        print(f"Rendered {render_path}")