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


import bpy, mathutils


def copy_vertex_colors(context, source, to_srgb=True, add_palette=False, use_vcpaint=False, layer=None):
    object = context.active_object
    if object.type == 'MESH' and object.mode == 'VERTEX_PAINT':
        mesh = object.data
        colors = mesh.vertex_colors.active.data
        index = 0

        if source == 'VCOLOR' and layer:
            try:
                srccols = mesh.vertex_colors[layer].data
            except KeyError:
                return False
        else:
            srccols = None

        if add_palette:
            palette = context.scene.tool_settings.vertex_paint.palette
            if not palette:
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
                        if source == 'BRUSH':
                            color = context.scene.tool_settings.vertex_paint.brush.color
                        elif source == 'DIFFUSE':
                            color = material.diffuse_color
                            if use_vcpaint:
                                material.use_vertex_color_paint = True
                        elif source == 'SPECULAR':
                            color = material.specular_color
                        elif source == 'LINE':
                            color = material.line_color[0:3]

                        if source in ('DIFFUSE', 'SPECULAR', 'LINE') and to_srgb:
                            # Linear to sRGB
                            color = mathutils.Color(L * 12.92 if L <= 0.0031308
                                                    else 1.055 * pow(L, 1.0 / 2.4) - 0.055 for L in color)

                        if palette:
                            for c in palette.colors:
                                if color == c.color:
                                    break
                            else:
                                pc = palette.colors.new()
                                pc.color = color

                if color or srccols:
                    for vertex in range(index, index + vertices):
                        colors[vertex].color = srccols[vertex].color if srccols else color

            index += vertices
    return True


# Operator

class PAINT_OT_vertex_color_copy(bpy.types.Operator):
    """Fill the active vertex color layer with colors copied from specified source"""
    bl_idname = "paint.vertex_color_copy"
    bl_label = "Copy Vertex Color"
    bl_options = {'REGISTER', 'UNDO'}

    source = bpy.props.EnumProperty(name="Color Source",
                                    description="Color source that will be copied to the active vertex color layer",
                                    items={('BRUSH', "Brush Color", "Use Paint Brush Color"),
                                           ('DIFFUSE', "Diffuse Color", "Use Material Diffuse Color"),
                                           ('SPECULAR', "Specular Color", "Use Material Spacular Color"),
                                           ('LINE', "Line Color", "Use Material Line Color"),
                                           ('VCOLOR', "Vertex Color Layer", "Copy Specified Vertex Color Layer")},
                                    default='DIFFUSE')
    to_srgb = bpy.props.BoolProperty(name="Convert to sRGB",
                                     description="Convert colors from linear to sRGB",
                                     default=True)
    add_palette = bpy.props.BoolProperty(name="Add to Palette",
                                         description="Add material colors to active palette",
                                         default=False)
    use_vcpaint = bpy.props.BoolProperty(name="Vertex Color Paint",
                                         description="Set \"Vertex Color Paint\" flag in each material",
                                         default=False)
    layer = bpy.props.StringProperty(name="Source Layer",
                                     description="Vertex color layer used as color source",
                                     default="")

    def execute(self, context):
        done = copy_vertex_colors(context, self.source,
                                  to_srgb=self.to_srgb, add_palette=self.add_palette,
                                  use_vcpaint=self.use_vcpaint, layer=self.layer)
        return {'FINISHED' if done else 'CANCELLED'}

    def draw(self, context):
        layout = self.layout
        col = layout.column()

        col.prop(self, "source")
        if self.source in ('DIFFUSE', 'SPECULAR', 'LINE'):
            col.prop(self, "to_srgb")
            col.prop(self, "add_palette")
        if self.source == 'DIFFUSE':
            col.prop(self, "use_vcpaint")
        if self.source == 'VCOLOR':
            col.prop_search(self, "layer", context.object.data, "vertex_colors")


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
