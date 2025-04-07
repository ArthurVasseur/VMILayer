import json
import xml.etree.ElementTree as ET
from evaluate_dependency import evaluate_dependency
import sys

exclude = {
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

platform_defines = {}
commands = {}
features = {}
processed_commands = []
extensions = {}

def parse_xml(xml_file):
    registry = ET.parse(xml_file).getroot()

    for platform in registry.findall("platforms/platform"):
        platform_defines[platform.attrib["name"]] = platform.attrib["protect"]



    for cmd in registry.findall("commands/command"):
        if "alias" in cmd.attrib:
            continue

        name = cmd.find("proto/name").text.strip()
        for object_type, functions in exclude.items():
            if name in functions:
                continue

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
                    is_array = True if "[" in child.tail and "]" in child.tail else False
                    parts.append(child.tail.strip())
            param_str = " ".join(parts).replace("  ", " ").strip()

            param_names.append(param_str.split(" ")[-1] if not is_array else param_str.split(" ")[-2])
            params.append(param_str)

        prototype = f"{return_value} {name}("
        if params:
            prototype += " "
            for i, p in enumerate(params):
                comma = "," if i < len(params) - 1 else ""
                prototype += f"{p}{comma} "
        prototype += ")"

        commands[name] = {
            "prototype": prototype,
            "name": name,
            "return_value": return_value if return_value != "void" else None,
            "param_names": param_names,
            "params": params,
            "kind": "instance" if (param_names and ("instance" in param_names[0]) or ("physicalDevice" in param_names[0])) else "device",
        }

    for feature in registry.findall("feature"):
        if "api" not in feature.attrib:
            continue
        api_version_define = None
        for require in feature.findall("require"):
            if api_version_define is None:
                for type_elem in require.findall("type"):
                    if "API_VERSION" in type_elem.attrib["name"]:
                        api_version_define = feature.attrib["name"]
                        break

            for command in require.findall("command"):
                name = command.attrib["name"]
                if name in processed_commands:
                    continue
                for object_type, functions in exclude.items():
                    if name in functions:
                        continue
                processed_commands.append(name)
                features[api_version_define] = features.get(api_version_define, []) + [commands[name]]

    for extension in registry.findall("extensions/extension"):
        if "disabled" in extension.attrib["supported"]:
            continue
        ext_name = extension.attrib["name"]
        depends = evaluate_dependency(extension.attrib["depends"]) if "depends" in extension.attrib else None
        platform = extension.attrib["platform"] if "platform" in extension.attrib else None
        cmds = []
        for require in extension.findall("require"):
            for command in require.findall("command"):
                name = command.attrib["name"]
                if name in processed_commands or name not in commands:
                    continue
                processed_commands.append(name)
                cmds.append(commands[name])

        extensions[ext_name] = {
            "depends": [] if depends is None else depends,
            "platform": None if platform is None else platform_defines[platform],
            "commands": cmds,
        }

def generate_cpp_code(defines: list[str], cmds: list[dict], f) -> None:
    defines_str = " && ".join([f"{d}" for d in defines if d])
    if defines and len(cmds) >= 1:
        f.write(f"#if {defines_str}\n")
    for cmd in cmds:
        if cmd["name"] in exclude["instance"] or cmd["name"] in exclude["device"]:
            continue
        f.write(f"{cmd['prototype']}\n{{\n")
        f.write(
            f"""    const auto* dp = VulkanMemoryInspector::GetInstance()->Get{cmd["kind"].title()}DispatchTable(GetKey({cmd['param_names'][0]}));
    if (!dp)
    {{
        CCT_ASSERT_FALSE("Could not get the device dispatch table");
        return {"VK_ERROR_INVALID_EXTERNAL_HANDLE" if cmd['return_value'] else ''};
    }}
    VulkanEvent vmiEvent = {{}};
    auto buff = Serialize(vmiEvent);
    VulkanMemoryInspector::GetInstance()->Send(buff);
    return dp->{cmd['name'][2:]}({', '.join(cmd['param_names'])});
""")
        f.write("}\n\n")
    if defines and len(cmds) >= 1:
        f.write(f"#endif // {defines_str}\n\n")

def generate_hpp_code(defines: list[str], cmds: list[dict], f) -> None:
    defines_str = ' && '.join([f'{d}' for d in defines if d])
    if defines and len(cmds) >= 1:
        f.write(f"#if {defines_str}\n")
    for cmd in cmds:
        return_value = cmd['return_value'] if cmd['return_value'] else 'void'
        prototype = cmd["name"] + "(" + ", ".join(cmd["params"]) + ")"
        f.write(f"VMI_EXPORT {return_value} VKAPI_CALL {prototype};\n")
    if defines and len(cmds) >= 1:
        f.write(f"#endif // {defines_str}\n\n")

def get_defines_list(ext, data):
    return [("defined(" + ext + ")")] + ([data["depends"]] if isinstance(data["depends"], str) else data["depends"]) + ([data["platform"]] if data["platform"] else [])

def generate_get_proc_addr_code(object_type: str, f):
    function_name = "vkGetDeviceProcAddr" if object_type == "VkDevice" else "vkGetInstanceProcAddr"
    f.write(f"PFN_vkVoidFunction {function_name}({object_type} instance, const char* pName)\n")
    f.write("{\n")
    for feature, cmds in features.items():
        defines_list = [feature]
        if feature in platform_defines:
            defines_list.append(platform_defines[feature])
        if defines_list and len(cmds) >= 1:
            f.write(f"#if {' && '.join(defines_list)}\n")
        for cmd in cmds:
            f.write(f"\tif (strcmp(pName, \"{cmd['name']}\") == 0)\n\t\treturn reinterpret_cast<PFN_vkVoidFunction>({cmd['name']});\n")
        if defines_list and len(cmds) >= 1:
            f.write(f"#endif // {' && '.join(defines_list)}\n")
    for ext, data in extensions.items():
        defines_list = get_defines_list(ext, data)
        if defines_list and len(data["commands"]) >= 1:
            f.write(f"#if {' && '.join(defines_list)}\n")
        for cmd in data["commands"]:
            f.write(f"\tif (strcmp(pName, \"{cmd['name']}\") == 0)\n\t\treturn reinterpret_cast<PFN_vkVoidFunction>({cmd['name']});\n")
        if defines_list and len(data["commands"]) >= 1:
            f.write(f"#endif // {' && '.join(defines_list)}\n")
    f.write(f"""
    const auto* dp = VulkanMemoryInspector::GetInstance()->Get{object_type[2:]}DispatchTable(GetKey(instance));
    if (!dp)
        return nullptr;
    return dp->{function_name[2:]}(instance, pName);
}}\n\n""")

def generate_cpp_file(file_path):
    with open(file_path, "w") as f:
        f.write("// This file is generated by gen_commands.py\n")
        f.write("#include <vulkan/vulkan.h>\n")
        f.write('#include "VMI/Defines.hpp"\n')
        f.write('#include "VMI/VulkanMemoryInspector.hpp"\n')
        f.write('#include "VMI/VulkanFunctions.hpp"\n')
        f.write('#include "VMI/Bindings.hpp"\n\n')
        f.write("// Core commands\n\n")
        for feature, cmds in features.items():
            generate_cpp_code([feature], cmds, f)
        f.write("// Extension commands\n\n")
        for ext, data in extensions.items():
            generate_cpp_code(get_defines_list(ext, data), data['commands'], f)

        generate_get_proc_addr_code('VkDevice', f)
        generate_get_proc_addr_code('VkInstance', f)


def generate_dispatch_table_members(object_type: str, f):
    for feature, cmds in features.items():
        f.write(f"#ifdef {feature}\n")
        for cmd in cmds:
            if cmd["kind"] == object_type:
                f.write(f'\tPFN_{cmd["name"]} {cmd["name"][2:]};\n')
        f.write(f"#endif // {feature}\n")

    for ext, data in extensions.items():
        defines_list = get_defines_list(ext, data)
        if defines_list and len(data["commands"]) >= 1:
            f.write(f"#if {' && '.join(defines_list)}\n")
        for cmd in data["commands"]:
            if cmd["kind"] == object_type:
                f.write(f'\tPFN_{cmd["name"]} {cmd["name"][2:]};\n')
        if defines_list and len(data["commands"]) >= 1:
            f.write(f"#endif // {' && '.join(defines_list)}\n")

def generate_hpp(file_path):
    with open(file_path, "w") as f:
        f.write("// This file is generated by gen_commands.py\n")
        f.write("#pragma once\n")
        f.write("#include <vulkan/vk_platform.h>\n")
        f.write("#include <vulkan/vulkan.h>\n")
        f.write('#include "VMI/Defines.hpp"\n')

        f.write('class InstanceDispatchTable\n{\n')
        f.write('\tpublic:\n')
        f.write('\t\tInstanceDispatchTable(VkInstance instance, PFN_vkGetInstanceProcAddr procAddr) {\n')
        for feature, cmds in features.items():
            f.write(f"#ifdef {feature}\n")
            for cmd in cmds:
                if cmd["kind"] == "instance":
                    f.write(f'\tthis->{cmd["name"][2:]} = reinterpret_cast<PFN_{cmd["name"]}>(procAddr(instance, "{cmd["name"]}"));\n')
            f.write(f"#endif // {feature}\n")
        for ext, data in extensions.items():
            defines_list = get_defines_list(ext, data)
            if defines_list and len(data["commands"]) >= 1:
                f.write(f"#if {' && '.join(defines_list)}\n")
            for cmd in data["commands"]:
                if cmd["kind"] == "instance":
                    f.write(f'\tthis->{cmd["name"][2:]} = reinterpret_cast<PFN_{cmd["name"]}>(procAddr(instance, "{cmd["name"]}"));\n')
            if defines_list and len(data["commands"]) >= 1:
                f.write(f"#endif // {' && '.join(defines_list)}\n")
        f.write('\t\t}\n')

        generate_dispatch_table_members("instance", f)
        f.write('};\n\n')

        f.write('class DeviceDispatchTable\n{\n')
        f.write('\tpublic:\n')
        f.write('\t\tDeviceDispatchTable(VkDevice device, PFN_vkGetDeviceProcAddr procAddr) {\n')
        for feature, cmds in features.items():
            f.write(f"#ifdef {feature}\n")
            for cmd in cmds:
                if cmd["kind"] == "device":
                    f.write(f'\tthis->{cmd["name"][2:]} = reinterpret_cast<PFN_{cmd["name"]}>(procAddr(device, "{cmd["name"]}"));\n')
            f.write(f"#endif // {feature}\n")

        for ext, data in extensions.items():
            defines_list = get_defines_list(ext, data)
            if defines_list and len(data["commands"]) >= 1:
                f.write(f"#if {' && '.join(defines_list)}\n")
            for cmd in data["commands"]:
                if cmd["kind"] == "device":
                    f.write(f'\tthis->{cmd["name"][2:]} = reinterpret_cast<PFN_{cmd["name"]}>(procAddr(device, "{cmd["name"]}"));\n')
            if defines_list and len(data["commands"]) >= 1:
                f.write(f"#endif // {' && '.join(defines_list)}\n")
        f.write('\t\t}\n')
        generate_dispatch_table_members("device", f)
        f.write('};\n\n')

        for feature, cmds in features.items():
            generate_hpp_code([feature], cmds, f)
        for ext, data in extensions.items():
            generate_hpp_code(get_defines_list(ext, data), data["commands"], f)

if __name__ == "__main__":
    # usage: python gen_commands.py <output_folder>
    if len(sys.argv) != 3:
        print("Usage: python gen_commands.py vk.xml <output_folder>")
        sys.exit(1)
    output_folder = sys.argv[2]
    xml_file = sys.argv[1]
    hpp_file_path = f"{output_folder}/VulkanCommands.hpp"
    cpp_file_path = f"{output_folder}/VulkanCommands.cpp"
    parse_xml(xml_file)
    generate_hpp(hpp_file_path)
    generate_cpp_file(cpp_file_path)

