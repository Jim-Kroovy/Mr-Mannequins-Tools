import bpy
import os

#---------- NOTES ------------------------------------------------------------------------------

# this script is a work in progress! (more may be needed for all material references to be written correctly with all node types)

#---------- FUNCTIONS --------------------------------------------------------------------------

# currently only gets references to images and node groups from materials with nodes...
def Get_References(mat):
    mat_refs = {}
    if mat.use_nodes:
        for node in mat.node_tree.nodes:
            if node.type == 'TEX_IMAGE':
                mat_refs[node.name] = node.image.name
            elif node.type == 'GROUP':
                mat_refs[node.name] = node.node_tree.name
    return mat_refs

# writes a reference clean up text...
def Write_References(mat, mat_refs):        
    text_name = mat.name + ".py"
    text = bpy.data.texts.new(text_name)
    text.write(f"""import bpy

mat_name = "{mat.name}"   
mat_refs = {mat_refs}

removal_refs = {{}}

mat = bpy.data.materials[mat_name]

for key in mat_refs:
    node = mat.node_tree.nodes[key]
    if node.type == 'TEX_IMAGE':
        if node.image.name != mat_refs[node.name]:
            removal_refs[node.image.name] = 'IMAGE'
            node.image = bpy.data.images[mat_refs[key]]
    elif node.type == 'GROUP':
        if node.node_tree.name != mat_refs[node.name]:
            removal_refs[node.node_tree.name] = 'GROUP'
            node.node_tree = bpy.data.node_groups[mat_refs[key]]
        
for key in removal_refs:
    if removal_refs[key] == 'IMAGE':
        bpy.data.images.remove(bpy.data.images[key], do_unlink=True)
    elif removal_refs[key] == 'GROUP':
        bpy.data.node_groups.remove(bpy.data.node_groups[key], do_unlink=True)
    
""")
    return text

# writes the material to a library .blend with its clean up script...
def Save_Material(mat, MMT):
    # gather references that might need cleaning up on load...
    mat_refs = Get_References(mat)
    # write reference clean up text...
    ref_text = Write_References(mat, mat_refs)
    # path to the created blend...
    mat_filepath = os.path.join(MMT.S_path, "MATERIAL_" + mat.name + ".blend")
    if MMT.A_pack_images:
        # pack images into blend file to save them with the material...
        for key in mat_refs:
            if mat_refs[key] in bpy.data.images:
                bpy.data.images[mat_refs[key]].pack()
    # write the .blend library...
    data_blocks = set([mat, ref_text])
    print(data_blocks)
    bpy.data.libraries.write(mat_filepath, data_blocks)
    # unlink the written text...
    copy_text = bpy.context.copy()
    copy_text['edit_text'] = ref_text
    bpy.ops.text.unlink(copy_text)
    if MMT.A_pack_images:
        # unpack the images afterwards using original files...
        for key in mat_refs:
            if mat_refs[key] in bpy.data.images:
                bpy.data.images[mat_refs[key]].unpack(method='USE_ORIGINAL')

#---------- EXECUTION --------------------------------------------------------------------------

def Stash(MMT, mat):
    # if the material is already in this stash...    
    if "MATERIAL_" + mat.name + ".blend" in os.listdir(MMT.S_path):
        # check if we want to overwrite it...
        if MMT.A_overwrite_existing_materials:
            # then overwrite it...
            Save_Material(mat, MMT)
        else:
            # or let the user know which material was already there...
            print(mat.name + " already exists and was not overwritten")
    else:
        # if material is not stashed, stash it...
        Save_Material(mat, MMT)

# function here for testing...      
#Stash(bpy.context.scene.JK_MMT, bpy.data.materials["M_UE4Man_Body"])