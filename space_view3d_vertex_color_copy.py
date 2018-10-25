# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

bl_info = {
    "name": "Vertex Color Copy",
    "author": "IRIE Shinsuke",
    "version": (0, 1),
    "blender": (2, 79, 0),
    "location": "View3D > Paint > Set Vertex Colors from Source",
    "description": "Fill the active vertex color layer with colors copied from specified source",
    "tracker_url": "https://github.com/iRi-E/blender_vertex_color_copy/issues",
    "category": "3D View",
}


import bpy
from mathutils import Color


def linear_to_srgb(color):
    return Color(L * 12.92 if L <= 0.0031308 else 1.055 * pow(L, 1.0 / 2.4) - 0.055 for L in color)

def srgb_to_linear(color):
    return Color(S / 12.92 if S <= 0.04045 else pow((S + 0.055) / 1.055, 2.4) for S in color)

def clamp_color(color):
    return Color((e if e >= 0 else 0.0 ) if e < 1.0 else 1.0 for e in color)

def blend_mix(origcol, blencol, factor):
    return clamp_color((1.0 - factor) * origcol + factor * blencol)

def blend_add(origcol, blencol, factor): # equivalent of linear dodge
    return clamp_color(origcol + factor * blencol)

def blend_subtract(origcol, blencol, factor):
    return clamp_color(origcol - factor * blencol)

def blend_multiply(origcol, blencol, factor):
    return blend_mix(origcol, Color(orig * blen for orig, blen in zip(origcol, blencol)), factor)

def blend_screen(origcol, blencol, factor):
    return blend_mix(origcol, Color(1.0 - (1.0 - orig) * (1.0 - blen) for orig, blen in zip(origcol, blencol)), factor)

def blend_lighten(origcol, blencol, factor):
    return blend_mix(origcol, Color(max(orig, blen) for orig, blen in zip(origcol, blencol)), factor)

def blend_darken(origcol, blencol, factor):
    return blend_mix(origcol, Color(min(orig, blen) for orig, blen in zip(origcol, blencol)), factor)

def blend_colordodge(origcol, blencol, factor):
    return blend_mix(origcol, Color(orig / (1.0 - min(blen, 0.9999999999)) # avoid division by zero
                                    for orig, blen in zip(origcol, blencol)), factor)

def blend_colorburn(origcol, blencol, factor):
    return blend_mix(origcol, Color(1.0 - (1.0 - orig) / max(blen, 0.0000000001) # avoid division by zero
                                    for orig, blen in zip(origcol, blencol)), factor)

def blend_linearburn(origcol, blencol, factor):
    return clamp_color(origcol + factor * (blencol - Color((1.0, 1.0, 1.0))))

def blend_overlay(origcol, blencol, factor):
    return blend_mix(origcol, Color(1.0 - 2.0 * (1.0 - orig) * (1.0 - blen) if orig > 0.5 else 2.0 * orig * blen
                                    for orig, blen in zip(origcol, blencol)), factor)

def blend_hardlight(origcol, blencol, factor):
    return blend_mix(origcol, Color(1.0 - 2.0 * (1.0 - orig) * (1.0 - blen) if blen > 0.5 else 2.0 * orig * blen
                                    for orig, blen in zip(origcol, blencol)), factor)

def blend_softlight(origcol, blencol, factor):
    return blend_mix(origcol, Color(1.0 - (1.0 - orig) * (1.5 - blen) if blen > 0.5 else orig * (blen + 0.5)
                                    for orig, blen in zip(origcol, blencol)), factor)

def blend_pinlight(origcol, blencol, factor):
    return blend_mix(origcol,  Color(max(orig, 2.0 * blen - 1.0) if blen > 0.5 else min(orig, 2.0 * blen)
                                     for orig, blen in zip(origcol, blencol)), factor)

def blend_vividlight(origcol, blencol, factor):
    return blend_mix(origcol,  Color(orig / (2.0 * (1.0 - min(blen, 0.9999999999))) if blen > 0.5
                                     else 1.0 - (1.0 - orig) / (2.0 * max(blen, 0.0000000001))
                                     for orig, blen in zip(origcol, blencol)), factor)

def blend_linearlight(origcol, blencol, factor):
    return clamp_color(origcol + factor * (2.0 * blencol - Color((1.0, 1.0, 1.0))))

def blend_difference(origcol, blencol, factor):
    return blend_mix(origcol, Color(abs(orig - blen) for orig, blen in zip(origcol, blencol)), factor)

def blend_exclusion(origcol, blencol, factor):
    return blend_mix(origcol, Color(orig + blen - 2.0 * orig * blen for orig, blen in zip(origcol, blencol)), factor)

def blend_color(origcol, blencol, factor):
    c = blencol
    c.v = origcol.v
    return c

def blend_hue(origcol, blencol, factor):
    c = origcol
    c.h = blencol.h
    return c

def blend_saturation(origcol, blencol, factor):
    c = origcol
    if c.s > 0.0005: # do nothing if black or white
        c.s = blencol.s
    return c

def blend_luminosity(origcol, blencol, factor):
    c = origcol
    c.v = blencol.v
    return c


blend_modes ={
    'REPLACE':None,
    'MIX':blend_mix,
    'ADD':blend_add,
    'SUBTRACT':blend_subtract,
    'MULTIPLY':blend_multiply,
    'SCREEN':blend_screen,
    'LIGHTEN':blend_lighten,
    'DARKEN':blend_darken,
    'COLORDODGE':blend_colordodge,
    'COLORBURN':blend_colorburn,
    'LINEARBURN':blend_linearburn,
    'OVERLAY':blend_overlay,
    'HARDLIGHT':blend_hardlight,
    'SOFTLIGHT':blend_softlight,
    'PINLIGHT':blend_pinlight,
    'VIVIDLIGHT':blend_vividlight,
    'LINEARLIGHT':blend_linearlight,
    'DIFFERENCE':blend_difference,
    'EXCLUSION':blend_exclusion,
    'COLOR':blend_color,
    'HUE':blend_hue,
    'SATURATION':blend_saturation,
    'LUMINOSITY':blend_luminosity,
}


def add_to_palette(palette, color): # color is sRGB
    for pc in palette.colors:
        if color == pc.color:
            return

    palette.colors.new().color = color


# Operator

class PAINT_OT_vertex_color_copy(bpy.types.Operator):
    """Fill the active vertex color layer with colors copied from specified source"""
    bl_idname = "paint.vertex_color_copy"
    bl_label = "Copy Vertex Color"
    bl_options = {'REGISTER', 'UNDO'}

    source = bpy.props.EnumProperty(name="Source Type",
                                    description="Color source that will be copied to the active vertex color layer",
                                    items=[
                                        ('UNIFORM', "Uniform Color", "Use Specified Uniform Color"),
                                        ('DIFFUSE', "Diffuse Color", "Use Material Diffuse Color"),
                                        ('SPECULAR', "Specular Color", "Use Material Spacular Color"),
                                        ('LINE', "Line Color", "Use Material Line Color"),
                                        ('VCOLOR', "Vertex Color Layer", "Copy Specified Vertex Color Layer"),
                                    ],
                                    default='DIFFUSE')
    color = bpy.props.FloatVectorProperty(name="Color",
                                          description="A color used for painting or blending",
                                          subtype='COLOR', # linear
                                          min=0.0,
                                          max=1.0,
                                          default=Color((1.0, 1.0, 1.0)))
    source_layer = bpy.props.StringProperty(name="Source Layer",
                                            description="Vertex color layer used as color source",
                                            default="")
    blend_mode = bpy.props.EnumProperty(name="Blend",
                                        description="How vertex colors in the mesh are affected by the blending tool",
                                        items=[
                                            ('REPLACE', "Replace", "Merely replace the vertex colors"),
                                            ('MIX', "Mix", "Use mix blending mode"),
                                            ('ADD', "Add", "Use add blending mode"),
                                            ('SUBTRACT', "Subtract", "Use subtract blending mode"),
                                            ('MULTIPLY', "Multiply", "Use multiply blending mode"),
                                            ('SCREEN', "Screen", "Use screen blending mode"),
                                            ('LIGHTEN', "Lighten", "Use lighten blending mode"),
                                            ('DARKEN', "Darken", "Use darken blending mode"),
                                            ('COLORDODGE', "Colordodge", "Use colordodge blending mode"),
                                            ('COLORBURN', "Colorburn", "Use colorburn blending mode"),
                                            ('LINEARBURN', "Linearburn", "Use linearburn blending mode"),
                                            ('OVERLAY', "Overlay", "Use overlay blending mode"),
                                            ('HARDLIGHT', "Hardlight", "Use hardlight blending mode"),
                                            ('SOFTLIGHT', "Softlight", "Use softlight blending mode"),
                                            ('PINLIGHT', "Pinlight", "Use pinlight blending mode"),
                                            ('VIVIDLIGHT', "Vividlight", "Use vividlight blending mode"),
                                            ('LINEARLIGHT', "Linearlight", "Use linearlight blending mode"),
                                            ('DIFFERENCE', "Difference", "Use difference blending mode"),
                                            ('EXCLUSION', "Exclusion", "Use exclusion blending mode"),
                                            ('COLOR', "Color", "Use color blending mode"),
                                            ('HUE', "Hue", "Use hue blending mode"),
                                            ('SATURATION', "Saturation", "Use saturation blending mode"),
                                            ('LUMINOSITY', "Luminosity", "Use luminosity blending mode"),
                                        ],
                                        default="REPLACE")
    blend_factor = bpy.props.FloatProperty(name="Factor",
                                           description="How powerful the effect of the blending tool is",
                                           soft_min=0.0,
                                           soft_max=1.0,
                                           default=1.0)
    add_palette = bpy.props.BoolProperty(name="Add to Palette",
                                         description="Add material colors to active palette",
                                         default=False)
    use_vcpaint = bpy.props.BoolProperty(name="Vertex Color Paint",
                                         description="Set \"Vertex Color Paint\" flag in each source material",
                                         default=False)

    def execute(self, context):
        object = context.active_object
        if object.type != 'MESH' or object.mode != 'VERTEX_PAINT':
            return {'CANCELLED'}

        mesh = object.data
        dstcols = mesh.vertex_colors.active.data
        index = 0
        blend_func = blend_modes[self.blend_mode]

        if self.color == None:
            self.color = srgb_to_linear(context.scene.tool_settings.vertex_paint.brush.color)

        if self.source == 'VCOLOR' and self.source_layer:
            try:
                srccols = mesh.vertex_colors[self.source_layer].data
            except KeyError:
                return {'CANCELLED'}
        else:
            srccols = None

        if self.add_palette:
            palette = context.scene.tool_settings.vertex_paint.palette

            if palette:
                if self.source == 'UNIFORM' and self.blend_mode != 'REPLACE':
                    ncol = len(palette.colors)
                    for k, pc in enumerate(palette.colors):
                        if k == ncol:
                            break
                        add_to_palette(palette,
                                       linear_to_srgb(blend_func(srgb_to_linear(pc.color), self.color, self.blend_factor)))
            else:
                palette = bpy.data.palettes.new("Palette")
                context.scene.tool_settings.vertex_paint.palette = palette
        else:
            palette = None

        for polygon in mesh.polygons:
            vertices = len(polygon.vertices)

            if not mesh.use_paint_mask or polygon.select:
                color = None

                if not srccols:
                    try:
                        material = object.material_slots[polygon.material_index].material
                    except IndexError:
                        material = None

                    if material:
                        if self.source == 'UNIFORM':
                            color = self.color
                        elif self.source == 'DIFFUSE':
                            color = material.diffuse_color
                            if self.use_vcpaint:
                                material.use_vertex_color_paint = True
                        elif self.source == 'SPECULAR':
                            color = material.specular_color
                        elif self.source == 'LINE':
                            color = material.line_color[0:3]

                if color and self.blend_mode == 'REPLACE':
                    color = linear_to_srgb(color)

                    if palette:
                        add_to_palette(palette, color)

                if color or srccols:
                    for vertex in range(index, index + vertices):
                        if self.blend_mode == 'REPLACE':
                            dstcols[vertex].color = color or srccols[vertex].color
                        else:
                            dstcols[vertex].color = linear_to_srgb(
                                blend_func(srgb_to_linear(dstcols[vertex].color),
                                           color or srgb_to_linear(srccols[vertex].color), self.blend_factor))

            index += vertices

        return {'FINISHED'}


    def draw(self, context):
        layout = self.layout

        box = layout.box()
        col = box.column()

        col.prop(self, "source")
        if self.source == 'UNIFORM':
            col.prop(self, "color", text="")
        if self.source == 'VCOLOR':
            col.prop_search(self, "source_layer", context.object.data, "vertex_colors")

        col.prop(self, "blend_mode")
        if self.blend_mode != "REPLACE":
            col.prop(self, "blend_factor", slider=True)

        col = layout.column()

        if self.source == 'UNIFORM' or self.source in ('DIFFUSE', 'SPECULAR', 'LINE') and self.blend_mode == 'REPLACE':
            col.prop(self, "add_palette")
        if self.source == 'DIFFUSE':
            col.prop(self, "use_vcpaint")


# Registration

def vertex_color_copy_button(self, context):
    self.layout.operator(
        PAINT_OT_vertex_color_copy.bl_idname,
        text="Set Vertex Colors from Source",
        icon='PLUGIN')

def register():
    bpy.utils.register_class(PAINT_OT_vertex_color_copy)
    bpy.types.VIEW3D_MT_paint_vertex.append(vertex_color_copy_button)


def unregister():
    bpy.utils.unregister_class(PAINT_OT_vertex_color_copy)
    bpy.types.VIEW3D_MT_paint_vertex.remove(vertex_color_copy_button)


if __name__ == "__main__":
    register()
