import json
import xml.etree.ElementTree as ET
from evaluate_dependency import evaluate_dependency
registry = ET.parse('./vk.xml').getroot()

platform_defines = {}
for platform in registry.findall('platforms/platform'):
    platform_defines[platform.attrib['name']] = platform.attrib['protect']

commands = {}
exclude = [
    'vkGetInstanceProcAddr',
    'vkGetDeviceProcAddr',
    'vkCreateInstance',
    'vkCreateDevice',
    'vkDestroyInstance',
    'vkDestroyDevice',
]

for cmd in registry.findall('commands/command'):
    if 'alias' in cmd.attrib:
        continue

    name = cmd.find('proto/name').text.strip()
    if name in commands or name in exclude:
        continue

    return_value = cmd.find('proto/type').text.strip()

    params = []
    param_names = []
    for param in cmd.findall('param'):
        parts = []
        if param.text:
            parts.append(param.text.strip())
        for child in param:
            parts.append(child.text.strip())
            if child.tail:
                parts.append(child.tail.strip())
        param_str = ' '.join(parts).replace('  ', ' ').strip()
        param_names.append(param_str.split(' ')[-1])
        params.append(param_str)

    prototype = f"{return_value} {name}("
    if params:
        prototype += " "
        for i, p in enumerate(params):
            comma = ',' if i < len(params) - 1 else ''
            prototype += f"{p}{comma} "
    prototype += ")"

    commands[name] = {
       'prototype': prototype,
       'name': name,
       'return_value': return_value if return_value != 'void' else None,
       'param_names': param_names,
    }

features = {}
processed_commands = []

for feature in registry.findall('feature'):
    if 'api' not in feature.attrib:
        continue
    api_version_define = None
    for require in feature.findall('require'):
        if api_version_define is None:
            for type_elem in require.findall('type'):
                if 'API_VERSION' in type_elem.attrib['name']:
                    api_version_define = feature.attrib['name']
                    break

        for command in require.findall('command'):
            name = command.attrib['name']
            if name in processed_commands or name in exclude:
                continue
            processed_commands.append(name)
            features[api_version_define] = features.get(api_version_define, []) + [commands[name]]

extensions = {}

for extension in registry.findall('extensions/extension'):
    if 'disabled' in extension.attrib['supported']:
        continue
    ext_name = extension.attrib['name']
    depends = evaluate_dependency(extension.attrib['depends']) if 'depends' in extension.attrib else None
    platform = extension.attrib['platform'] if 'platform' in extension.attrib else None
    cmds = []
    for require in extension.findall('require'):
        for command in require.findall('command'):
            name = command.attrib['name']
            if name in processed_commands or name not in commands:
                continue
            processed_commands.append(name)
            cmds.append(commands[name])
    extensions[ext_name] = {
        'depends': [] if depends is None else depends,
        'platform': None if platform is None else platform_defines[platform],
        'commands': cmds,
    }

def generate_cpp_code(defines: list[str], cmds: list[dict]) -> None:
    defines_str = ' && '.join([f'{d}' for d in defines if d])
    if defines and len(cmds) > 1:
        f.write(f'#if {defines_str}\n')
    for cmd in cmds:
        f.write(f"{cmd['prototype']}\n{{\n")
        f.write(
            f"""    const auto* dp = VulkanMemoryInspector::GetInstance()->GetDeviceDispatchTable(GetKey({cmd['param_names'][0]}));
    if (!dp)
    {{
        CCT_ASSERT_FALSE("Could not get the device dispatch table");
        return {"VK_ERROR_INVALID_EXTERNAL_HANDLE" if cmd['return_value'] else ''};
    }}
    VulkanEvent vmiEvent = {{}};
    auto buff = Serialize(vmiEvent);
    VulkanMemoryInspector::GetInstance()->Send(buff);
    return dp->{cmd['name']}({', '.join(cmd['param_names'])});
""")
        f.write("}\n\n")
    if defines and len(cmds) > 1:
        f.write(f"#endif // {defines_str}\n\n")

def generate_dispatch_table_code(instance_function, device_function, f):
    f.write('struct InstanceDispatchTable\n{\n')
    for cmd, data in instance_function.items():
        if data['defines']:
            f.write(f'#if {data['defines']}\n')
        f.write(f'\tPFN_{cmd} {cmd};\n')
        if data['defines']:
            f.write(f'#endif // {data['defines']}\n')
    f.write('};\n\n')

    f.write('struct DeviceDispatchTable\n{\n')
    for cmd, data in device_function.items():
        if data['defines']:
            f.write(f'#if {data['defines']}\n')
        f.write(f'\tPFN_{cmd} {cmd};\n')
        if data['defines']:
            f.write(f'#endif // {data['defines']}\n')
    f.write('};\n\n')

def generate_hpp_code(defines: list[str], cmds: list[dict]) -> None:
    defines_str = ' && '.join([f'{d}' for d in defines if d])
    if defines and len(cmds) > 1:
        f.write(f'#if {defines_str}\n')
    for cmd in cmds:
        f.write(f'VMI_EXPORT {cmd['return_value'] if cmd['return_value'] else 'void'} VKAPI_CALL {cmd['prototype']};)\n')
    if defines and len(cmds) > 1:
        f.write(f"#endif // {defines_str}\n\n")

def get_defines_list(data):
    return ([data['depends']] if isinstance(data['depends'], str) else data['depends']) + ([data['platform']] if data['platform'] else [])

def generate_get_proc_addr_code(object_type: str, f):
    function_name = 'vkGetDeviceProcAddr' if object_type == 'VkDevice' else 'vkGetInstanceProcAddr'
    f.write(f'VMI_EXPORT PFN_vkVoidFunction VKAPI_CALL {function_name}({object_type} instance, const char* pName)\n')
    f.write('{\n')
    for feature, cmds in features.items():
        defines_list = [feature]
        if feature in platform_defines:
            defines_list.append(platform_defines[feature])
        if defines_list and len(cmds) > 1:
            f.write(f'#if {" && ".join(defines_list)}\n')
        for cmd in cmds:
            f.write(f'\tVMI_GET_PROC_ADDR({cmd['name']});\n')
        if defines_list and len(cmds) > 1:
            f.write(f'#endif // {" && ".join(defines_list)}\n')
    for ext, data in extensions.items():
        defines_list = get_defines_list(data)
        if defines_list and len(data['commands']) > 1:
            f.write(f'#if {" && ".join(defines_list)}\n')
        for cmd in data['commands']:
            f.write(f'\tVMI_GET_PROC_ADDR({cmd['name']});\n')
        if defines_list and len(data['commands']) > 1: 
            f.write(f'#endif // {" && ".join(defines_list)}\n')
    f.write(f'''
    const auto* dp = VulkanMemoryInspector::GetInstance()->Get{object_type[2:]}DispatchTable(GetKey(instance));
    if (!dp)
        return nullptr;
    return dp->{function_name}(instance, pName);
}}\n\n''')
    
with open('commands.cpp', 'w') as f:
    f.write('// This file is generated by gen_commands.py\n')
    f.write('#include <vulkan/vulkan.h>\n')
    f.write('#include "VMI/Defines.hpp"\n')
    f.write('#include "VMI/VulkanMemoryInspector.hpp"\n')
    f.write('#include "VMI/Bindings.hpp"\n\n')
    f.write('// Core commands\n\n')
    for feature, cmds in features.items():
        generate_cpp_code([feature], cmds)
    f.write('// Extension commands\n\n')
    for ext, data in extensions.items():
        defines_list =     ([data['depends']] if isinstance(data['depends'], str) else data['depends']) + ([data['platform']] if data['platform'] else [])
        generate_cpp_code(defines_list, data['commands'])
    
    generate_get_proc_addr_code('VkDevice', f)
    generate_get_proc_addr_code('VkInstance', f)

with open('commands.hpp', 'w') as f:
    f.write('// This file is generated by gen_commands.py\n')
    f.write('#pragma once\n')
    f.write('#include <vulkan/vulkan.h>\n')
    f.write('#include "VMI/Defines.hpp"\n')

    instance_functions = {}
    device_functions = {}

    for feature, cmds in features.items():
        for cmd in cmds:
            if cmd['param_names'] and 'instance' in cmd['param_names'][0]:
                instance_functions[cmd['name']] = {
                    'defines': ' && '.join([f'{d}' for d in feature if d]),
                }
            if cmd['param_names'] and len(cmd['param_names']) >= 1:
                device_functions[cmd['name']] = {
                    'defines': ' && '.join([f'{d}' for d in feature if d]),
                }
    for ext, data in extensions.items():
        for cmd in data['commands']:
            if cmd['param_names'] and 'instance' in cmd['param_names'][0]:
                instance_functions[cmd['name']] = {
                    'defines': get_defines_list(data),
                }
            if cmd['param_names'] and len(cmd['param_names']) >= 1:
                device_functions[cmd['name']] = {
                    'defines': get_defines_list(data),
                }
    generate_dispatch_table_code(instance_functions, device_functions, f)

    for feature, cmds in features.items():
        generate_hpp_code([feature], cmds)
    for ext, data in extensions.items():
        generate_hpp_code(get_defines_list(data), data['commands'])