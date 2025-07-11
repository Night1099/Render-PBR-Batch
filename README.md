This has been superseded ands I reccomend using this project with CookToleranceBRDF method https://github.com/giuvecchio/PyPBR



## Blender Diffuse-Albedo Renderer

The goal of these scripts is to render paired albedo and diffuse textures for training AI models.

Use this command to run the scripts:
```blender.exe --background --python 'path\to\script.py' -- 'path\to\source\folder'```

The scripts expect the following folder structure:
```
- Root
-- Textures
--- texture1
---- texture1_diffuse.png
---- texture1_metallic.png
---- texture1_normal.png
---- texture1_roughness.png
---- texture1_height.png
--- texture2
etc.
```

### Notes:
- Blender by default requires OpenGL Normal maps. DX Normal maps require conversion prior to usage
- This was last tested on Blender 4.1
