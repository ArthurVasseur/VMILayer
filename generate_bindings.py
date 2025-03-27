#!/usr/bin/env python3
import json
import os

type_mapping = {
    "i32": {"cpp": "cct::Int32", "rust": "i32", "sql": "INTEGER"},
    "i64": {"cpp": "cct::Int64", "rust": "i64", "sql": "BIGINT"},
    "str": {"cpp": "std::string", "rust": "String", "sql": "TEXT"}
}

def snake_to_camel(name: str) -> str:
    return "".join(word.capitalize() for word in name.split('_'))

def snake_to_field(name: str) -> str:
    parts = name.split('_')
    return parts[0].lower() + "".join(word.capitalize() for word in parts[1:])

def generate_cpp_binding(table: dict) -> str:
    class_name = snake_to_camel(table["name"])
    code = []
    code.append(f"class {class_name} {{")
    code.append("public:")
    for col in table["columns"]:
        cpp_type = type_mapping[col["type"]]["cpp"]
        field_name = snake_to_field(col["name"])
        code.append(f"\t{cpp_type} {field_name};")
    code.append("")
    code.append("\tstd::vector<cct::Byte> serialize() const {")
    code.append("\t\tsize_t total_size = 0;")
    for col in table["columns"]:
        field_name = snake_to_field(col["name"])
        if col["type"] == "str":
            code.append(f"\t\ttotal_size += sizeof(cct::UInt32) + {field_name}.size();")
        else:
            cpp_type = type_mapping[col["type"]]["cpp"]
            code.append(f"\t\ttotal_size += sizeof({cpp_type});")
    code.append("\t\tstd::vector<cct::Byte> buffer(total_size);")
    code.append("\t\tsize_t offset = 0;")
    for col in table["columns"]:
        cpp_type = type_mapping[col["type"]]["cpp"]
        field_name = snake_to_field(col["name"])
        if col["type"] == "str":
            code.append(f'\t\tcct::UInt32 len_{field_name} = static_cast<cct::UInt32>({field_name}.size());')
            code.append(f'\t\tlen_{field_name} = cct::ByteSwap(len_{field_name});')
            code.append(f'\t\tstd::memcpy(buffer.data() + offset, &len_{field_name}, sizeof(cct::UInt32));')
            code.append(f'\t\toffset += sizeof(cct::UInt32);')
            code.append(f'\t\tstd::memcpy(buffer.data() + offset, {field_name}.data(), {field_name}.size());')
            code.append(f'\t\toffset += {field_name}.size();')
        else:
            code.append(f'\t\t{cpp_type} temp_{field_name} = cct::ByteSwap({field_name});')
            code.append(f'\t\tstd::memcpy(buffer.data() + offset, &temp_{field_name}, sizeof({cpp_type}));')
            code.append(f'\t\toffset += sizeof({cpp_type});')
    code.append("\t\treturn buffer;")
    code.append("\t}")
    code.append("")
    code.append(f'\tstatic {class_name} deserialize(std::span<const cct::Byte> buffer) {{')
    code.append(f'\t\t{class_name} obj;')
    code.append("\t\tsize_t offset = 0;")
    for col in table["columns"]:
        cpp_type = type_mapping[col["type"]]["cpp"]
        field_name = snake_to_field(col["name"])
        if col["type"] == "str":
            code.append(f'\t\tcct::UInt32 len_{field_name};')
            code.append(f'\t\tstd::memcpy(&len_{field_name}, buffer.data() + offset, sizeof(cct::UInt32));')
            code.append(f'\t\tlen_{field_name} = cct::ByteSwap(len_{field_name});')
            code.append(f'\t\toffset += sizeof(cct::UInt32);')
            code.append(f'\t\tobj.{field_name}.assign(reinterpret_cast<const char*>(buffer.data() + offset), len_{field_name});')
            code.append(f'\t\toffset += len_{field_name};')
        else:
            code.append(f'\t\t{cpp_type} temp_{field_name};')
            code.append(f'\t\tstd::memcpy(&temp_{field_name}, buffer.data() + offset, sizeof({cpp_type}));')
            code.append(f'\t\tobj.{field_name} = cct::ByteSwap(temp_{field_name});')
            code.append(f'\t\toffset += sizeof({cpp_type});')
    code.append("\t\treturn obj;")
    code.append("\t}")
    code.append("};")
    return "\n".join(code)

def generate_rust_binding(table: dict) -> str:
    struct_name = snake_to_camel(table["name"])
    lines = []
    lines.append("#[derive(Debug, Serialize, Deserialize)]")
    lines.append(f"pub struct {struct_name} {{")
    for col in table["columns"]:
        rust_type = type_mapping[col["type"]]["rust"]
        field_name = col["name"]
        lines.append(f"    pub {field_name}: {rust_type},")
    lines.append("}")
    lines.append("")
    lines.append(f"impl {struct_name} {{")
    lines.append("    pub fn serialize(&self) -> Vec<u8> {")
    lines.append("        let mut total_size = 0;")
    for col in table["columns"]:
        field_name = col["name"]
        if col["type"] == "str":
            lines.append(f"        total_size += 4 + self.{field_name}.len();")
        else:
            rust_type = type_mapping[col["type"]]["rust"]
            lines.append(f"        total_size += std::mem::size_of::<{rust_type}>();")
    lines.append("        let mut buffer = Vec::with_capacity(total_size);")
    for col in table["columns"]:
        field_name = col["name"]
        if col["type"] == "str":
            lines.append(f'        let {field_name}_bytes = self.{field_name}.as_bytes();')
            lines.append(f"        let len = {field_name}_bytes.len() as u32;")
            lines.append("        buffer.extend(&len.to_le_bytes());")
            lines.append(f"        buffer.extend({field_name}_bytes);")
        else:
            lines.append(f"        buffer.extend(&self.{field_name}.to_le_bytes());")
    lines.append("        buffer")
    lines.append("    }")
    lines.append("")
    lines.append("    pub fn deserialize(buffer: &[u8]) -> Self {")
    lines.append("        let mut offset = 0;")
    default_fields = []
    for col in table["columns"]:
        field_name = col["name"]
        rust_type = type_mapping[col["type"]]["rust"]
        if col["type"] == "str":
            lines.append(f"        let len = u32::from_le_bytes(buffer[offset..offset+4].try_into().unwrap()) as usize;")
            lines.append("        offset += 4;")
            lines.append(f"        let {field_name} = String::from_utf8(buffer[offset..offset+len].to_vec()).unwrap();")
            lines.append("        offset += len;")
            default_fields.append(f"{field_name}")
        else:
            lines.append(f"        let {field_name} = {rust_type}::from_le_bytes(buffer[offset..offset+std::mem::size_of::<{rust_type}>()].try_into().unwrap());")
            lines.append(f"        offset += std::mem::size_of::<{rust_type}>();")
            default_fields.append(f"{field_name}")
    lines.append(f"        Self {{ {', '.join(default_fields)} }}")
    lines.append("    }")
    lines.append("}")
    return "\n".join(lines)

def generate_sql_schema(table: dict) -> str:
    lines = []
    table_name = table["name"]
    lines.append(f"CREATE TABLE {table_name} (")
    col_lines = []
    for col in table["columns"]:
        sql_type = type_mapping[col["type"]]["sql"]
        line = f"    {col['name']} {sql_type}"
        if col.get("primary_key", False):
            line += " PRIMARY KEY"
            if col.get("autoincrement", False):
                line += " AUTOINCREMENT"
        if col.get("not_null", False):
            line += " NOT NULL"
        col_lines.append(line)
    lines.append(",\n".join(col_lines))
    lines.append(");")
    return "\n".join(lines)

def write_to_file(filename: str, content: str):
    output_dir = os.path.dirname(filename)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)

def generate_cpp_file(json_data: dict) -> str:
    header = (
        "/// This file is generated by generate_bindings.py\n"
        "/// Do not edit manually\n"
        "#pragma once\n"
        "#include <cstdint>\n"
        "#include <vector>\n"
        "#include <string>\n"
        "#include <cstring>\n"
        "#include <variant>\n"
        "#include <span>\n"
        "#include <Concerto/Core/ByteSwap.hpp>\n\n"
    )
    classes = []
    classes.append(f"enum class EventType {{")
    for i, value in enumerate(json_data["tables"]):
        classes.append(f"\t{snake_to_camel(value['name'])} = {i},")
    classes.append("};")
    classes.append("\n")

    
    for table in json_data["tables"]:
        classes.append(generate_cpp_binding(table))
        classes.append("\n")
    
    code = "inline std::variant<std::monostate, "
    for klass in json_data["tables"]:
        code += f"{snake_to_camel(klass['name'])}, "
    code = code[:-2] + "> Deserialize(const std::vector<cct::Byte>& data) {\n"
    code += "\tdecltype(Deserialize(data)) res;\n"
    code += "\tif (data.size() < sizeof(cct::UInt32)) return res;\n"
    code += "\tcct::UInt32 type;\n"
    code += "\tstd::memcpy(&type, data.data(), sizeof(cct::UInt32));\n"
    code += "\ttype = cct::ByteSwap(type);\n"
    code += "\tswitch (type) {\n"
    for i, table in enumerate(json_data["tables"]):
        code += f"\t\tcase {i}:\n"
        code += f"\t\t\tres = {snake_to_camel(table['name'])}::deserialize(std::span<const cct::Byte>(data.data() + sizeof(cct::UInt32), data.size() - sizeof(cct::UInt32)));\n"
        code += "\t\t\tbreak;\n"
    code += "\t\tdefault:\n"
    code += "\t\t\tbreak;\n"
    code += "\t}\n"
    code += "\treturn res;\n"
    code += "}\n\n"

    code += "template<typename T>\n"
    code += "inline std::vector<cct::Byte> Serialize(const T& obj) {\n"
    code += "\tstd::vector<cct::Byte> buffer;\n"
    code += "\tbuffer.reserve(sizeof(cct::UInt32));\n"
    for table in json_data["tables"]:
        code += f"\tif constexpr (std::is_same_v<T, {snake_to_camel(table['name'])}>) {{\n"
        code += f"\t\tcct::UInt32 type = static_cast<cct::UInt32>(EventType::{snake_to_camel(table['name'])});\n"
        code += "\t\ttype = cct::ByteSwap(type);\n"
        code += "\t\tstd::memcpy(buffer.data(), &type, sizeof(cct::UInt32));\n"
        code += "\t\tauto serializedType = obj.serialize();\n"
        code += "\t\tbuffer.insert(buffer.end(), serializedType.begin(), serializedType.end());\n"
        code += "\t\treturn buffer;\n"
        code += "\t}\n"
    code += "\treturn buffer;\n"
    code += "}\n\n"
    return header + "\n".join(classes) + "\n" + code

def generate_rust_file(json_data: dict) -> str:
    modules = []
    for table in json_data["tables"]:
        modules.append(generate_rust_binding(table))
        modules.append("\n")
    return "\n".join(modules)

def generate_sql_file(json_data: dict) -> str:
    code = "pub const DATABASE_SCHEMA: &str = r###\""
    for table in json_data["tables"]:
        code += generate_sql_schema(table)
        code += "\n"
    code += "\"###;\n\n"
    return code

def main():
    args = os.sys.argv
    if len(args) != 4:
        print("Usage: python generate_bindings.py lang output_file json_file")
        return

    lang = args[1]
    output_file = args[2]
    json_file = args[3]
    if lang not in ["cpp", "rust"]:
        print("Invalid language")
        return

    with open(json_file, "r", encoding="utf-8") as f:
        json_data = json.load(f)
        if lang == "cpp":
            content = generate_cpp_file(json_data)
            write_to_file(output_file, content)
        elif lang == "rust":
            content = generate_sql_file(json_data) + generate_rust_file(json_data)
            write_to_file(output_file, content)

if __name__ == "__main__":
    main()
