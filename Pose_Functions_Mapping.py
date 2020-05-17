import bpy
import re
                                        
# writes current mapping to a text... (will be needed to replace custom mapping after updates)
def Write_Mapping(mapping):
    text = bpy.data.texts.new("MMT_Mapping.py")
    text.write("""import bpy
# we need a reference to the mapping in the add-on preferences...
mapping = bpy.context.preferences.addons["MrMannequinsTools"].preferences.Mapping
# the custom mapping that we wrote to this text file...""")
    text.write("\ncustom_mapping = {\n")
    # for each part in the mapping...
    for part in mapping:
        # format the part line...
        text.write('\t("{p_name}", "{p_index}", "{p_side}") :\n'.format(p_name=part.Part, p_index=part.First, p_side=part.Second))
        # for each section of the part...
        for i1, joint in enumerate(part.Joints):
            # get the syntax needed for the start of joint entry...
            start = ("{" if i1 == 0 else "")
            # format joint line...
            text.write('\t    {syntax}("{s_name}", "{s_index}", "{s_side}") : [\n'.format(s_name=joint.Joint, s_index=joint.First, s_side=joint.Second, syntax=start))
            # for each section in the joint...
            for i2, section in enumerate(joint.Sections):
                # get the syntax needed for the end of section list + end of joint dictionary...
                end = ("]}," if i2 == (len(joint.Sections) - 1) and i1 == (len(part.Joints) - 1) else "]," if i2 == (len(joint.Sections) - 1) else ",")
                # format the name line...
                text.write('\t        ("{strings[0]}", "{strings[1]}", "{strings[2]}"){syntax}\n'.format(strings=[section.Section, section.First, section.Second], syntax=end))
    # close the entire dictionary...
    text.write("    }\n\n")
    # wirte the operator to re-add the written retargets when the script gets run...
    text.write("""# then when we run this...
mapping.clear()
# iterate through new mapping dictionary...
for part, joints in custom_mapping.items():
    # add the part...
    part_data = mapping.add()
    part_data.Part = part[0]
    part_data.First = part[1]
    part_data.Second = part[2]
    # iterate through part joints...
    for joint, sections in joints.items():
        # add the joint...
        joint_data = part_data.Joints.add()
        joint_data.Joint = joint[0]
        joint_data.First = joint[1]
        joint_data.Second = joint[2]
        # iterate over joints sections...
        for section in sections:
            # add the section...
            section_data = joint_data.Sections.add()
            section_data.Section = section[0]
            section_data.First = section[1]
            section_data.Second = section[2]""")

# adds a dictionary of a 3 dimensional array to the current mapping...
def Set_New_Mapping(mapping, new_dict, clear):
    # if we want to clear current mapping first...
    if clear:
        mapping.clear()
    # iterate through new mapping dictionary...
    for part, joints in new_dict.items():
        # add the part...
        part_data = mapping.add()
        part_data.Part = part[0]
        part_data.First = part[1]
        part_data.Second = part[2]
        # iterate through part joints...
        for joint, sections in joints.items():
            # add the joint...
            joint_data = part_data.Joints.add()
            joint_data.Joint = joint[0]
            joint_data.First = joint[1]
            joint_data.Second = joint[2]
            # iterate over joints sections...
            for section in sections:
                # add the section...
                section_data = joint_data.Sections.add()
                section_data.Section = section[0]
                section_data.First = section[1]
                section_data.Second = section[2]

# gets the full name from mapping indices...
def Get_Mapping_Name(indices, mapping):
    end = ["", "", ""]
    # if the part index is a valid...
    if indices[0] in range(0, len(mapping)):
        part = mapping[indices[0]]
        end[0] = part.Second
        # get the part name... (checking if the second suffix is L or R or nothing)
        p_name = part.Part + ("_" if part.First != "" else "") + part.First + ("_" + end[0] if end[0].upper() not in ["L", "R", ""] else "")
        # if the joint index is valid...
        if indices[1] in range(0, len(mapping[indices[0]].Joints)):
            joint = mapping[indices[0]].Joints[indices[1]]
            end[1] = joint.Second
            # get the joint name... (checking if the second suffix is L or R or nothing)
            j_name = joint.Joint + ("_" if joint.First != "" else "") + joint.First + ("_" + end[1] if end[1].upper() not in ["L", "R", ""] else "")
            # if the section index is valid...
            if indices[2] in range(0, len(mapping[indices[0]].Joints[indices[1]].Sections)):
                section = mapping[indices[0]].Joints[indices[1]].Sections[indices[2]]
                end[2] = section.Second
                # get the section name... (checking if the second suffix is L or R or nothing)
                s_name = section.Section + ("_" if section.First != "" else "") + section.First + ("_" + end[2] if end[2].upper() not in ["L", "R", ""] else "")
            else:
                s_name = ""
        else:
            j_name = ""
            s_name = ""
    else:
        p_name = ""
        j_name = ""
        s_name = ""
    # figure out what the suffix should be if there were any side based siffices... (priority == Part > Joint > Section)
    suffix = end[0] if end[0].upper() in ["L", "R"] else end[1] if end[1].upper() in ["L", "R"] else end[2] if end[2].upper() in ["L", "R"] else ""
    # combine all three names and the suffix...
    name = p_name + ("_" if j_name != "" else "") + j_name + ("_" if s_name != "" else "") + s_name + ("_" if suffix != "" else "") + suffix
    # and return the full name...
    return name

    #("Arm", "Front", "Upper")
        #("Wrist", "02", "R")
            #("Carpus", "01", "L")

        # accumulated... 
        #"Arm_Front_Upper_Wrist_02_R_Carpus_01_L", # might not mirror
        # appended second suffices...  
        #"Arm_Front_Wrist_02_Carpus_01_Upper_R_L", # might not mirror
        # appended first and second suffices..
        #"Arm_Carpus_Wrist_Front_02_01_L_R_L",
        # appended second suffices, no duplicate ending...
        #"Arm_Front_Wrist_02_Carpus_01_R_L"
        # appended first and second suffices, no duplicate ending...
        #"Arm_Carpus_Wrist_Front_02_01_R_L",
        # accumulated acounting for _L and _R...  
        #"Arm_Front_Upper_Wrist_02_Carpus_01_R",
          

