#!/usr/bin/env python
"""
Extended generator for Vulkan commands and Vulkan structs-to-JSON conversion.

This tool now supports:
   1. Generating Vulkan dispatch tables/command wrappers (existing functionality).
   2. Generating C++ functions that serialize Vulkan structs to JSON using nlohmann/json.
   3. Making the generated ToJSON functions feature- and extension-aware,
      wrapping them in #ifdef/#endif guards based on the Vulkan XML spec.

Usage:
    python gen_commands.py <vk.xml> <output_folder>
"""

import sys
import xml.etree.ElementTree as ET
from abc import ABC, abstractmethod
from evaluate_dependency import evaluate_dependency

# -----------------------------------------------------------------------------
# Global constants for excluding commands
# -----------------------------------------------------------------------------

EXCLUDE = {
    "instance": [
        "vkGetInstanceProcAddr",
        "vkGetDeviceProcAddr",
        "vkCreateInstance",
        "vkCreateDevice",
        "vkDestroyInstance",
        "vkDestroyDevice",
    ],
    "device": [
        "vkQueuePresentKHR"
    ]
}

# -----------------------------------------------------------------------------
# Vulkan Registry Parser
# -----------------------------------------------------------------------------

class VulkanRegistryParser:
    """
    Parses the Vulkan XML registry (vk.xml) and produces a dictionary with:
       - platform_defines
       - commands
       - features
       - extensions
       - structs
       - structs_features: mapping struct name to list of feature macros (e.g. VK_VERSION_1_0)
       - structs_extensions: mapping struct name to list of extension macros (e.g. VK_KHR_swapchain)
    """
    def __init__(self, xml_vk_file, xml_video_file):
        self.xml_vk_file = xml_vk_file
        self.xml_video_file = xml_video_file
        self.platform_defines = {}
        self.commands = {}
        self.features = {}
        self.extensions = {}
        self.structs = {}
        self.processed_commands = []
        self.structs_features = {}
        self.structs_extensions = {}
        self.handles = []

    def parse(self):
        xml_vk_file_tree = ET.parse(self.xml_vk_file).getroot()
        xml_video_file_tree = ET.parse(self.xml_video_file).getroot()

        for child in xml_video_file_tree:
            xml_vk_file_tree.append(child)

        registry = xml_vk_file_tree
        self._parse_platforms(registry)
        self._parse_commands(registry)
        self._parse_features(registry)
        self._parse_extensions(registry)
        self._parse_structs(registry)
        return {
            "platform_defines": self.platform_defines,
            "commands": self.commands,
            "features": self.features,
            "extensions": self.extensions,
            "structs": self.structs,
            "structs_features": self.structs_features,
            "structs_extensions": self.structs_extensions,
            "handles": self.handles,
        }

    def _parse_platforms(self, registry):
        for platform in registry.findall("platforms/platform"):
            self.platform_defines[platform.attrib["name"]] = platform.attrib["protect"]

    def _parse_commands(self, registry):
        for cmd in registry.findall("commands/command"):
            if "alias" in cmd.attrib:
                continue
            name = cmd.find("proto/name").text.strip()
            return_value = cmd.find("proto/type").text.strip()
            params = []
            param_names = []
            for param in cmd.findall("param"):
                if "api" in param.attrib and param.attrib["api"] != "vulkan":
                    continue
                parts = []
                if param.text:
                    parts.append(param.text.strip())
                is_array = False
                for child in param:
                    parts.append(child.text.strip())
                    if child.tail:
                        if "[" in child.tail and "]" in child.tail:
                            is_array = True
                        parts.append(child.tail.strip())
                param_str = " ".join(parts).replace("  ", " ").strip()
                name_index = -2 if is_array else -1
                param_names.append(param_str.split(" ")[name_index])
                params.append(param_str)
            prototype = f"{return_value} {name}("
            if params:
                prototype += " " + ", ".join(params) + " "
            prototype += ")"
            cmd_kind = "instance" if (param_names and ("instance" in param_names[0] or "physicalDevice" in param_names[0])) else "device"
            self.commands[name] = {
                "prototype": prototype,
                "name": name,
                "return_value": return_value if return_value != "void" else None,
                "param_names": param_names,
                "param_types": (p.split(",")[:2] for p in params),
                "params": params,
                "kind": cmd_kind,
            }

    def _parse_features(self, registry):
        for feature in registry.findall("feature"):
            if "api" not in feature.attrib:
                continue
            feature_name = feature.attrib["name"]
            # Process types required by this feature.
            for require in feature.findall("require"):
                for type_elem in require.findall("type"):
                    tname = type_elem.attrib.get("name")
                    if not tname and type_elem.text:
                        tname = type_elem.text.strip()
                    if tname:
                        self.structs_features.setdefault(tname, []).append(f"defined({feature_name})")
                for command in require.findall("command"):
                    name = command.attrib["name"]
                    if name in self.processed_commands:
                        continue
                    self.processed_commands.append(name)
                    self.features.setdefault(feature_name, []).append(self.commands[name])

    def _parse_extensions(self, registry):
        for extension in registry.findall("extensions/extension"):
            if "disabled" in extension.attrib.get("supported", ""):
                continue
            ext_name = extension.attrib["name"]
            depends = evaluate_dependency(extension.attrib["depends"]) if "depends" in extension.attrib else None
            platform = self.platform_defines[extension.attrib.get("platform")] if extension.attrib.get("platform") else None
            cmds = []
            for require in extension.findall("require"):
                # Process types required by this extension.
                for type_elem in require.findall("type"):
                    tname = type_elem.attrib.get("name")
                    if not tname and type_elem.text:
                        tname = type_elem.text.strip()
                    if tname:
                        self.structs_extensions.setdefault(tname, []).append([(f"defined({ext_name})")] + ([depends] if depends else []) + [platform] + ([evaluate_dependency(require.attrib["depends"])] if "depends" in require.attrib else []))
                for command in require.findall("command"):
                    name = command.attrib["name"]
                    if name in self.processed_commands or name not in self.commands:
                        continue
                    self.processed_commands.append(name)
                    cmds.append(self.commands[name])
            self.extensions[ext_name] = {
                "depends": [] if depends is None else depends,
                "platform": None if platform is None else self.platform_defines.get(platform),
                "commands": cmds,
            }

    def _parse_structs(self, registry):
        """
        Parses <type> elements with category="struct" from the <types> block.
        For each struct, collect its name and its member definitions.
        """
        self.structs = {}
        for t in registry.findall("types/type"):
            if "disabled" in t.attrib.get("supported", ""):
                continue
            if t.attrib.get("category") == "handle":
                name = t.get("name")
                if name:
                    self.handles.append(name)
                else:
                    name = t.find("name")
                    if name is not None:
                        self.handles.append(name.text.strip())
                        name = name.text.strip()
                continue
            if t.attrib.get("category") != "struct" and t.attrib.get("category") != "union":
                continue
            struct_name = t.get("name")
            if not struct_name:
                name_elem = t.find("name")
                if name_elem is not None:
                    struct_name = name_elem.text.strip()
            if not struct_name:
                continue
            if struct_name in ["VkNativeBufferUsage2ANDROID", "VkNativeBufferANDROID", "VkSwapchainImageCreateInfoANDROID", "VkPhysicalDevicePresentationPropertiesANDROID", "VkAndroidHardwareBufferFormatProperties2ANDROID"]:
                continue
            member_elems = t.findall("member")
            if not member_elems:
                continue
            members = []
            for m in member_elems:
                type_elem = m.find("type")
                member_name_elem = m.find("name")
                if type_elem is None or member_name_elem is None:
                    continue
                mtype = type_elem.text.strip()
                mname = member_name_elem.text.strip()
                # Determine if the member is a pointer.
                full_text = "".join(m.itertext())
                is_pointer = "*" in full_text
                # Check if the member is an array.
                mtext = m.tail or ""
                array_len = None
                if "[" in mtext and "]" in mtext:
                    try:
                        array_len = mtext.split("[")[1].split("]")[0].strip()
                    except Exception:
                        array_len = None
                members.append({
                    "type": mtype,
                    "name": mname,
                    "is_pointer": is_pointer,
                    "array_len": array_len,
                })
            self.structs[struct_name] = {
                "name": struct_name,
                "members": members,
            }

# -----------------------------------------------------------------------------
# Base Generator for Code Generation
# -----------------------------------------------------------------------------

class BaseGenerator(ABC):
    """
    Base interface for any code generator. New targets like JSON generators can
    implement this interface.
    """
    def __init__(self, registry_data):
        self.registry_data = registry_data

    @abstractmethod
    def generate(self, output_file):
        pass

def get_defines_list(ext, data):
    depends = data["depends"] if isinstance(data["depends"], list) else [data["depends"]] if data["depends"] else []
    platform = [data["platform"]] if data["platform"] else []
    return [f"defined({ext})"] + depends + platform

# -----------------------------------------------------------------------------
# C++ Command Generators
# -----------------------------------------------------------------------------

class CppCommandGenerator(BaseGenerator):
    """
    Generates the C++ source file for Vulkan command wrappers.
    """
    def generate(self, output_file):
        with open(output_file, "w") as f:
            f.write("// This file is generated by gen_commands.py\n")
            f.write("#include <vulkan/vulkan.h>\n")
            f.write('#include "VMI/Defines.hpp"\n')
            f.write('#include "VMI/VulkanMemoryInspector.hpp"\n')
            f.write('#include "VMI/VulkanFunctions.hpp"\n')
            f.write('#include "VMI/Bindings.hpp"\n\n')
            f.write('#include "VMI/VulkanStructToJson.hpp"\n\n')
            f.write("// Core commands\n\n")
            for feature, cmds in self.registry_data["features"].items():
                self._generate_cpp_code([feature], cmds, f)
            f.write("// Extension commands\n\n")
            for ext, data in self.registry_data["extensions"].items():
                self._generate_cpp_code(get_defines_list(ext, data), data["commands"], f)

            self._generate_get_proc_addr_code('VkDevice', f)
            self._generate_get_proc_addr_code('VkInstance', f)

    def _generate_cpp_code(self, defines, cmds, f):
        defines_str = " && ".join([str(d) for d in defines if d])
        if defines and cmds:
            f.write(f"#if {defines_str}\n")
        for cmd in cmds:
            if cmd["name"] in EXCLUDE.get("instance", []) or cmd["name"] in EXCLUDE.get("device", []):
                continue
            json_data = "{"
            for pname, ptype in zip(cmd['param_names'], cmd['param_types']):
                ptype = ptype[0]
                ptype = ptype.replace(pname, "").strip()
                is_pointer = "*" in ptype
                if is_pointer:
                    if ptype in self.registry_data["structs"]:
                        json_data += f'{{"{pname}", *{pname}}}'
                    else:
                        json_data += f'{{"{pname}", reinterpret_cast<uintptr_t>({pname})}}'
                else:
                    if ptype in self.registry_data["handles"]:
                        json_data += f'{{"{pname}", reinterpret_cast<uintptr_t>({pname})}}'
                    else:
                        json_data += f'{{"{pname}", {pname}}}'
                if pname != cmd['param_names'][-1]:
                    json_data += ", "
            json_data += "}"
            f.write(f"{cmd['prototype']}\n{{\n")
            f.write(
f"""	const auto* dp = VulkanMemoryInspector::GetInstance()->Get{cmd["kind"].title()}DispatchTable(GetKey({cmd['param_names'][0]}));
	if (!dp)
	{{
		CCT_ASSERT_FALSE("Could not get the device dispatch table");
		return {"VK_ERROR_INVALID_EXTERNAL_HANDLE" if cmd['return_value'] else ''};
	}}
	{"auto result = " if cmd["return_value"] != None else ""}dp->{cmd['name'][2:]}({', '.join(cmd['param_names'])});
	VulkanEvent vmiEvent = {{
		.id = 0,
		.timestamp = GetCurrentTimeStamp(),
		.frameNumber = VulkanMemoryInspector::GetInstance()->GetFrameIndex(),
		.functionName = "{cmd['name']}",
		.parameters = nlohmann::json{json_data}.dump(),
		.resultCode = {"static_cast<cct::Int32>(result)" if cmd["return_value"] != None else "0"},
		.threadId = GetCurrentThreadId(),
    }};
	auto buff = Serialize(vmiEvent);
	VulkanMemoryInspector::GetInstance()->Send(buff);
	{"return result;" if cmd["return_value"] != None else ""};
}}\n\n""")
        if defines and cmds:
            f.write(f"#endif // {defines_str}\n\n")


    def _generate_get_proc_addr_code(self, object_type, f):
        function_name = "vkGetDeviceProcAddr" if object_type == "VkDevice" else "vkGetInstanceProcAddr"
        f.write(f"PFN_vkVoidFunction {function_name}({object_type} instance, const char* pName)\n")
        f.write("{\n")
        for feature, cmds in self.registry_data["features"].items():
            defines_list = [feature]
            if feature in self.registry_data["platform_defines"]:
                defines_list.append(self.registry_data["platform_defines"][feature])
            if defines_list and cmds:
                f.write(f"#if {' && '.join(defines_list)}\n")
            for cmd in cmds:
                f.write(f'\tif (strcmp(pName, "{cmd["name"]}") == 0)\n\t\treturn reinterpret_cast<PFN_vkVoidFunction>({cmd["name"]});\n')
            if defines_list and cmds:
                f.write(f"#endif // {' && '.join(defines_list)}\n")
        for ext, data in self.registry_data["extensions"].items():
            defines_list = get_defines_list(ext, data)
            if defines_list and data["commands"]:
                f.write(f"#if {' && '.join(defines_list)}\n")
            for cmd in data["commands"]:
                f.write(f'\tif (strcmp(pName, "{cmd["name"]}") == 0)\n\t\treturn reinterpret_cast<PFN_vkVoidFunction>({cmd["name"]});\n')
            if defines_list and data["commands"]:
                f.write(f"#endif // {' && '.join(defines_list)}\n")
        f.write(f"""
    const auto* dp = VulkanMemoryInspector::GetInstance()->Get{object_type[2:]}DispatchTable(GetKey(instance));
    if (!dp)
        return nullptr;
    return dp->{function_name[2:]}(instance, pName);
}}\n\n""")

class HppCommandGenerator(BaseGenerator):
    """
    Generates the C++ header file for dispatch table classes and command wrapper declarations.
    """
    def generate(self, output_file):
        with open(output_file, "w") as f:
            f.write("// This file is generated by gen_commands.py\n")
            f.write("#pragma once\n")
            f.write("#include <vulkan/vk_platform.h>\n")
            f.write("#include <vulkan/vulkan.h>\n")
            f.write('#include "VMI/Defines.hpp"\n')
            # Dispatch table classes for Instance and Device
            self._generate_instance_dispatch(f)
            self._generate_device_dispatch(f)
            # Command declarations for features and extensions
            for feature, cmds in self.registry_data["features"].items():
                self._generate_hpp_code([feature], cmds, f)
            for ext, data in self.registry_data["extensions"].items():
                self._generate_hpp_code(get_defines_list(ext, data), data["commands"], f)

    def _generate_instance_dispatch(self, f):
        f.write('class InstanceDispatchTable\n{\npublic:\n')
        f.write('\tInstanceDispatchTable(VkInstance instance, PFN_vkGetInstanceProcAddr procAddr) {\n')
        for feature, cmds in self.registry_data["features"].items():
            f.write(f"#ifdef {feature}\n")
            for cmd in cmds:
                if cmd["kind"] == "instance":
                    f.write(f'\t\tthis->{cmd["name"][2:]} = reinterpret_cast<PFN_{cmd["name"]}>(procAddr(instance, "{cmd["name"]}"));\n')
            f.write(f"#endif // {feature}\n")
        for ext, data in self.registry_data["extensions"].items():
            defines_list = get_defines_list(ext, data)
            if defines_list and data["commands"]:
                f.write(f"#if {' && '.join(defines_list)}\n")
            for cmd in data["commands"]:
                if cmd["kind"] == "instance":
                    f.write(f'\t\tthis->{cmd["name"][2:]} = reinterpret_cast<PFN_{cmd["name"]}>(procAddr(instance, "{cmd["name"]}"));\n')
            if defines_list and data["commands"]:
                f.write(f"#endif // {' && '.join(defines_list)}\n")
        f.write('\t}\n')
        self._generate_dispatch_table_members("instance", f)
        f.write('};\n\n')

    def _generate_device_dispatch(self, f):
        f.write('class DeviceDispatchTable\n{\npublic:\n')
        f.write('\tDeviceDispatchTable(VkDevice device, PFN_vkGetDeviceProcAddr procAddr) {\n')
        for feature, cmds in self.registry_data["features"].items():
            f.write(f"#ifdef {feature}\n")
            for cmd in cmds:
                if cmd["kind"] == "device":
                    f.write(f'\t\tthis->{cmd["name"][2:]} = reinterpret_cast<PFN_{cmd["name"]}>(procAddr(device, "{cmd["name"]}"));\n')
            f.write(f"#endif // {feature}\n")
        for ext, data in self.registry_data["extensions"].items():
            defines_list = get_defines_list(ext, data)
            if defines_list and data["commands"]:
                f.write(f"#if {' && '.join(defines_list)}\n")
            for cmd in data["commands"]:
                if cmd["kind"] == "device":
                    f.write(f'\t\tthis->{cmd["name"][2:]} = reinterpret_cast<PFN_{cmd["name"]}>(procAddr(device, "{cmd["name"]}"));\n')
            if defines_list and data["commands"]:
                f.write(f"#endif // {' && '.join(defines_list)}\n")
        f.write('\t}\n')
        self._generate_dispatch_table_members("device", f)
        f.write('};\n\n')

    def _generate_dispatch_table_members(self, object_type, f):
        for feature, cmds in self.registry_data["features"].items():
            f.write(f"#ifdef {feature}\n")
            for cmd in cmds:
                if cmd["kind"] == object_type:
                    f.write(f'\tPFN_{cmd["name"]} {cmd["name"][2:]};\n')
            f.write(f"#endif // {feature}\n")
        for ext, data in self.registry_data["extensions"].items():
            defines_list = get_defines_list(ext, data)
            if defines_list and data["commands"]:
                f.write(f"#if {' && '.join(defines_list)}\n")
            for cmd in data["commands"]:
                if cmd["kind"] == object_type:
                    f.write(f'\tPFN_{cmd["name"]} {cmd["name"][2:]};\n')
            if defines_list and data["commands"]:
                f.write(f"#endif // {' && '.join(defines_list)}\n")

    def _generate_hpp_code(self, defines, cmds, f):
        defines_str = " && ".join([str(d) for d in defines if d])
        if defines and cmds:
            f.write(f"#if {defines_str}\n")
        for cmd in cmds:
            return_value = cmd['return_value'] if cmd['return_value'] else 'void'
            prototype = cmd["name"] + "(" + ", ".join(cmd["params"]) + ")"
            f.write(f"VMI_EXPORT {return_value} VKAPI_CALL {prototype};\n")
        if defines and cmds:
            f.write(f"#endif // {defines_str}\n\n")

# -----------------------------------------------------------------------------
# Struct-to-JSON Generators
# -----------------------------------------------------------------------------

def flatten(lst):
    """Recursively flatten a nested list and filter out None values."""
    for item in lst:
        if isinstance(item, list):
            yield from flatten(item)
        elif item is not None:
            yield item

class HppStructJsonGenerator(BaseGenerator):
    """
    Generates a header file with declarations for ToJSON functions for Vulkan structs.
    Each declaration is wrapped with #ifdef guards if the struct is associated with specific
    Vulkan features or extensions.
    """
    def generate(self, output_file):
        structs_features = self.registry_data.get("structs_features", {})
        structs_extensions = self.registry_data.get("structs_extensions", {})
        with open(output_file, "w") as f:
            f.write("// This file is generated by gen_commands.py\n")
            f.write("#pragma once\n")
            f.write("#include <vulkan/vulkan.h>\n")
            f.write("#include <nlohmann/json.hpp>\n\n")
            # Forward declarations for each struct conversion function.
            for struct_name in self.registry_data["structs"]:
                # Determine any associated macros from features/extensions.
                feature_guards = structs_features.get(struct_name, [])
                ext_guards = structs_extensions.get(struct_name, [])
                all_guards = feature_guards + ext_guards
                if all_guards:
                    guard_str = " && ".join(list(flatten(all_guards)))
                    f.write(f"#if {guard_str}\n")
                f.write(f"void to_json(nlohmann::json& j, const {struct_name}& value);\n")
                if all_guards:
                    f.write(f"#endif // {guard_str}\n\n")
                else:
                    f.write("\n")

class CppStructJsonGenerator(BaseGenerator):
    """
    Generates a source file with definitions for ToJson functions for Vulkan structs.
    Each definition is wrapped with #ifdef guards if the struct is associated with specific
    Vulkan features or extensions.
    """
    def generate(self, output_file):
        # Capture the set of Vulkan struct names to detect nested types.
        struct_names = set(self.registry_data["structs"].keys())
        structs_features = self.registry_data.get("structs_features", {})
        structs_extensions = self.registry_data.get("structs_extensions", {})
        handles = set(self.registry_data.get("handles", []))
        with open(output_file, "w") as f:
            f.write("// This file is generated by gen_commands.py\n")
            f.write('#include "VulkanStructToJson.hpp"\n')
            f.write("#include <nlohmann/json.hpp>\n\n")
            # For each struct, generate a ToJson function.
            for struct_name, struct_data in self.registry_data["structs"].items():
                # Collect any feature or extension macros associated with the struct.
                feature_guards = structs_features.get(struct_name, [])
                ext_guards = structs_extensions.get(struct_name, [])
                all_guards = [feature_guards[0]] if feature_guards else [] + ext_guards
                if all_guards:
                    guard_str = " && ".join(list(flatten(all_guards)))
                    f.write(f"#if {guard_str}\n")
                f.write(f"void to_json(nlohmann::json& j, const {struct_name}& value) {{\n")
                last_member = struct_data["members"][-1]
                for member in struct_data["members"]:
                    mname = member["name"]
                    mtype = member["type"]
                    # If the member is an array, generate a loop.
                    if member["array_len"]:
                        f.write(f"\tj[\"{mname}\"] = nlohmann::json::array();\n")
                        f.write(f"\tfor (size_t i = 0; i < {member['array_len']}; i++) {{\n")
                        f.write(f"\t\tj[\"{mname}\"].push_back(value.{mname}[i]);\n")
                        f.write("\t}\n")
                    elif "PFN_" in mtype:
                        f.write(f"\tj[\"{mname}\"] = value.{mname} ? reinterpret_cast<intptr_t>(value.{mname}) : 0;\n")
                    elif mtype in handles:
                        f.write(f"\tj[\"{mname}\"] = value.{mname} ? reinterpret_cast<uintptr_t>(value.{mname}) : 0;\n")
                    elif member["is_pointer"]:
                        if mname.startswith("pp"):
                            f.write(f"""
	if (value.{mname})
		j[\"{mname}\"] = std::span(reinterpret_cast<const {mtype}*>(value.{mname}), value.{last_member});
	else
		j[\"{mname}\"] = std::span(reinterpret_cast<const {mtype}*>(nullptr), 0);\n
""")
                        elif mtype == "void":
                            f.write(f"\tj[\"{mname}\"] = value.{mname} ? reinterpret_cast<intptr_t>(value.{mname}) : 0;\n")
                        elif mtype == "char":
                            f.write(f"\tif (value.{mname})\n\t\tj[\"{mname}\"] = value.{mname};\n\telse\n\t\t j[\"{mname}\"] = {mtype}();\n")
                        else:
                            if mtype in struct_names:
                                f.write(f"\tif (value.{mname})\n\t\tj[\"{mname}\"] = *value.{mname};\n\telse\n\t\t j[\"{mname}\"] = {mtype}();\n")
                            else:
                                f.write(f"\tif (value.{mname})\n\t\tj[\"{mname}\"] = *value.{mname};\n\telse\n\t\t j[\"{mname}\"] = {mtype}();\n")
                    elif mtype in struct_names:
                        f.write(f"\tj[\"{mname}\"] = value.{mname};\n")
                    else:
                        f.write(f"\tj[\"{mname}\"] = value.{mname};\n")
                    last_member = mname
                f.write("}\n\n")
                if all_guards:
                    f.write(f"#endif // {guard_str}\n\n")

# -----------------------------------------------------------------------------
# Generator Factory
# -----------------------------------------------------------------------------

class GeneratorFactory:
    """
    Factory to retrieve the appropriate generator based on a type string.
    """
    @staticmethod
    def get_generator(generator_type, registry_data):
        if generator_type == "cpp":
            return CppCommandGenerator(registry_data)
        elif generator_type == "hpp":
            return HppCommandGenerator(registry_data)
        elif generator_type == "struct_json_hpp":
            return HppStructJsonGenerator(registry_data)
        elif generator_type == "struct_json_cpp":
            return CppStructJsonGenerator(registry_data)
        else:
            raise ValueError(f"Unknown generator type: {generator_type}")

# -----------------------------------------------------------------------------
# Main entry point
# -----------------------------------------------------------------------------

def main():
    if len(sys.argv) != 4:
        print("Usage: python gen_commands.py <vk.xml> <video.xml> <output_folder>")
        sys.exit(1)
    xml_vk_file = sys.argv[1]
    xml_video_file = sys.argv[2]
    output_folder = sys.argv[3]

    # Parse the Vulkan registry XML.
    parser = VulkanRegistryParser(xml_vk_file, xml_video_file)
    registry_data = parser.parse()

    # Generate command header and source files (existing functionality).
    hpp_generator = GeneratorFactory.get_generator("hpp", registry_data)
    hpp_file_path = f"{output_folder}/VulkanCommands.hpp"
    hpp_generator.generate(hpp_file_path)

    cpp_generator = GeneratorFactory.get_generator("cpp", registry_data)
    cpp_file_path = f"{output_folder}/VulkanCommands.cpp"
    cpp_generator.generate(cpp_file_path)

    # Generate struct-to-JSON header and source files (new functionality).
    struct_hpp_generator = GeneratorFactory.get_generator("struct_json_hpp", registry_data)
    struct_hpp_path = f"{output_folder}/VulkanStructToJson.hpp"
    struct_hpp_generator.generate(struct_hpp_path)

    struct_cpp_generator = GeneratorFactory.get_generator("struct_json_cpp", registry_data)
    struct_cpp_path = f"{output_folder}/VulkanStructToJson.cpp"
    struct_cpp_generator.generate(struct_cpp_path)

if __name__ == "__main__":
    main()
