#
# "Vertex Color Copy" scripting example
#

# * transfer material colors (diffuse, specular) to vertex color layers
# * all of mesh objects in the scene will be processed
# * we assume "Col" is partially being used to specify diffuse colors
# * diffuse and specular colors will be stored in "Diffuse" and "Specular"
#   layers, respectively
# * set "Vertex Color Paint" flag in each source material
# * create palettes and add the transferred material colors to them

import bpy
from mathutils import Color
D = bpy.data
C = bpy.context

for m in D.meshes:

    # select an object that m is bound to if possible, or skip if not
    for o in C.scene.objects:
        if o.data == m:
            C.scene.objects.active = o
            saved_mode = o.mode
            break
    else:
        continue

    # set interaction mode "Vertex Paint" temporarily
    bpy.ops.object.mode_set(mode='VERTEX_PAINT')

    # activate "Col" layer
    if m.vertex_colors.get("Col"):
        vc = m.vertex_colors["Col"]
        m.vertex_colors["Col"].active = True
    else:
        vc = None

    # select polygons that vertex colors are not used yet
    m.use_paint_mask = False
    if vc:
        i = 0
        for p in m.polygons:
            n = len(p.vertices)
            p.select=False
            for v in range(i, i + n):
                if vc.data[v].color != Color((1.0, 1.0, 1.0)):
                    m.use_paint_mask = True
                    break
            else:
                p.select=True
            i += n

    # create palette for the mesh if not existing
    try:
        C.tool_settings.vertex_paint.palette = D.palettes[m.name]
    except KeyError:
        C.tool_settings.vertex_paint.palette = D.palettes.new(m.name)

    # create "Diffuse" layer
    if m.vertex_colors.get("Diffuse"):
        m.vertex_colors.remove(m.vertex_colors["Diffuse"]) # remove existing "Diffuse"
    m.vertex_colors.new("Diffuse") # copied from "Col"

    # copy diffuse colors from materials assigned to each polygon
    m.vertex_colors["Diffuse"].active = True
    bpy.ops.paint.vertex_color_copy(source='DIFFUSE', add_palette=True, use_vcpaint=True)

    # create "Specular" layer
    if m.vertex_colors.get("Specular"):
        m.vertex_colors.remove(m.vertex_colors["Specular"]) # remove existing "Specular"
    m.vertex_colors.new("Specular") # copied from "Diffuse"

    # copy specular colors from materials assigned to each polygon
    m.use_paint_mask = False
    m.vertex_colors["Specular"].active = True
    bpy.ops.paint.vertex_color_copy(source='SPECULAR', add_palette=True)

    # activate "Diffuse" layer to use for rendering
    if m.vertex_colors.get("Diffuse"):
        m.vertex_colors["Diffuse"].active = True
        m.vertex_colors["Diffuse"].active_render = True

    # restore saved interaction mode
    bpy.ops.object.mode_set(mode=saved_mode)
