## Very old version of script

import bpy
import sys
import os

source_folder = sys.argv[5] 

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
                    material.node_tree.links.new(normal_map.outputs['Normal'], shader.inputs['Normal'])
                elif tex_type == "Roughness":
                    material.node_tree.links.new(tex_image.outputs['Color'], shader.inputs['Roughness'])
                elif tex_type == "Metallic":
                    material.node_tree.links.new(tex_image.outputs['Color'], shader.inputs['Metallic'])
                elif tex_type == "Height":
                    displacement = nodes.new('ShaderNodeDisplacement')
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

        bpy.ops.object.light_add(type='SUN', radius=5, location=(0, 0, 5))
        sun_light = bpy.context.object.data
        sun_light.energy = 10  # Increase this value to make the light brighter

        bpy.context.scene.cycles.device = 'GPU'

        prefs = bpy.context.preferences
        cprefs = prefs.addons['cycles'].preferences
        cprefs.get_devices()
        cprefs.compute_device_type = 'OPTIX'

        for device in cprefs.devices:
            device.use = True 

        bpy.context.scene.render.engine = 'CYCLES'
        bpy.context.scene.render.resolution_x = 4096
        bpy.context.scene.render.resolution_y = 4096
        render_path = os.path.join(folder_path, 'render.png')
        bpy.context.scene.render.filepath = render_path

        bpy.ops.render.render(write_still=True)
        print(f"Rendered {render_path}")