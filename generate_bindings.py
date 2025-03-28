#!/usr/bin/env python3
import json
import os
import sys

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

def is_optional(col: dict) -> bool:
    # Treat primary keys as non-optional even if not marked not_null.
    return not (col.get("not_null", False) or col.get("primary_key", False))

def generate_rust_binding(table: dict) -> str:
    struct_name = snake_to_camel(table["name"])
    code = []
    # Struct definition
    code.append(f"#[derive(Debug)]")
    code.append(f"pub struct {struct_name} {{")
    for col in table["columns"]:
        rust_type = type_mapping[col["type"]]["rust"]
        field_name = col["name"]
        if is_optional(col):
            rust_type = f"Option<{rust_type}>"
        code.append(f"    pub {field_name}: {rust_type},")
    code.append("}\n")

    # Implementation block with serialize() and deserialize()
    code.append(f"impl {struct_name} {{")
    # Serialization
    code.append("    pub fn serialize(&self) -> Vec<u8> {")
    code.append("        let mut buffer = Vec::new();")
    for col in table["columns"]:
        col_type = col["type"]
        field_name = col["name"]
        optional = is_optional(col)
        if optional:
            code.append(f"        // Serialize optional field: {field_name}")
            code.append(f"        if let Some(ref value) = self.{field_name} {{")
            code.append("            buffer.push(1);")
            if col_type in ["i32", "i64"]:
                code.append(f"            buffer.extend(&value.to_be_bytes());")
            elif col_type == "str":
                # For a string, first write u32 length then the bytes
                code.append("            let s_bytes = value.as_bytes();")
                code.append("            let s_len = s_bytes.len() as u32;")
                code.append("            buffer.extend(&s_len.to_be_bytes());")
                code.append("            buffer.extend(s_bytes);")
            code.append("        } else {")
            code.append("            buffer.push(0);")
            code.append("        }")
        else:
            code.append(f"        // Serialize field: {field_name}")
            if col_type in ["i32", "i64"]:
                code.append(f"        buffer.extend(&self.{field_name}.to_be_bytes());")
            elif col_type == "str":
                code.append(f"        let s_bytes = self.{field_name}.as_bytes();")
                code.append("        let s_len = s_bytes.len() as u32;")
                code.append("        buffer.extend(&s_len.to_be_bytes());")
                code.append("        buffer.extend(s_bytes);")
    code.append("        buffer")
    code.append("    }")
    code.append("")
    # Deserialization
    code.append("    pub fn deserialize(data: &[u8]) -> Option<Self> {")
    code.append("        let mut offset = 0;")
    field_values = []
    for col in table["columns"]:
        col_type = col["type"]
        field_name = col["name"]
        optional = is_optional(col)
        if optional:
            code.append(f"        // Deserialize optional field: {field_name}")
            code.append("        if offset + 1 > data.len() { return None; }")
            code.append("        let flag = data[offset];")
            code.append("        offset += 1;")
            code.append(f"        let {field_name} = if flag == 1 {{")
            if col_type in ["i32"]:
                code.append("            if offset + 4 > data.len() { return None; }")
                code.append("            let val = i32::from_be_bytes(data[offset..offset+4].try_into().ok()?);")
                code.append("            offset += 4;")
                code.append("            Some(val)")
            elif col_type in ["i64"]:
                code.append("            if offset + 8 > data.len() { return None; }")
                code.append("            let val = i64::from_be_bytes(data[offset..offset+8].try_into().ok()?);")
                code.append("            offset += 8;")
                code.append("            Some(val)")
            elif col_type == "str":
                code.append("            if offset + 4 > data.len() { return None; }")
                code.append("            let len = u32::from_be_bytes(data[offset..offset+4].try_into().ok()?);")
                code.append("            offset += 4;")
                code.append("            if offset + (len as usize) > data.len() { return None; }")
                code.append("            let s = String::from_utf8(data[offset..offset+(len as usize)].to_vec()).ok()?;")
                code.append("            offset += len as usize;")
                code.append("            Some(s)")
            code.append("        } else { None };")
            field_values.append(field_name)
        else:
            code.append(f"        // Deserialize field: {field_name}")
            if col_type in ["i32"]:
                code.append("        if offset + 4 > data.len() { return None; }")
                code.append(f"        let {field_name} = i32::from_be_bytes(data[offset..offset+4].try_into().ok()?);")
                code.append("        offset += 4;")
            elif col_type in ["i64"]:
                code.append("        if offset + 8 > data.len() { return None; }")
                code.append(f"        let {field_name} = i64::from_be_bytes(data[offset..offset+8].try_into().ok()?);")
                code.append("        offset += 8;")
            elif col_type == "str":
                code.append("        if offset + 4 > data.len() { return None; }")
                code.append("        let len = u32::from_be_bytes(data[offset..offset+4].try_into().ok()?);")
                code.append("        offset += 4;")
                code.append("        if offset + (len as usize) > data.len() { return None; }")
                code.append(f"        let {field_name} = String::from_utf8(data[offset..offset+(len as usize)].to_vec()).ok()?;")
                code.append("        offset += len as usize;")
            field_values.append(field_name)
    # Build the struct with all fields
    code.append(f"        Some({struct_name} {{")
    for field in field_values:
        code.append(f"            {field},")
    code.append("        })")
    code.append("    }")
    code.append("}")
    return "\n".join(code)

def generate_rust_file(json_data: dict) -> str:
    header = (
        "// This file is generated by generate_bindings.py\n"
        "// Do not edit manually\n"
        "\n"
        "use std::convert::TryInto;\n\n"
    )
    bindings = []
    # Generate bindings for each table
    for table in json_data["tables"]:
        bindings.append(generate_rust_binding(table))
        bindings.append("\n")
    
    # Generate the Packet enum with dispatching on a u32 command id.
    bindings.append("#[derive(Debug)]")
    bindings.append("pub enum Packet {")
    for i, table in enumerate(json_data["tables"]):
        variant = snake_to_camel(table["name"])
        bindings.append(f"    {variant}({variant}),")
    bindings.append("}\n")
    
    bindings.append("impl Packet {")
    # Serialization: prepend a 4-byte command id (big-endian) then the serialized data.
    bindings.append("    pub fn serialize(&self) -> Vec<u8> {")
    bindings.append("        let mut buffer = Vec::new();")
    bindings.append("        match self {")
    for i, table in enumerate(json_data["tables"]):
        variant = snake_to_camel(table["name"])
        bindings.append(f"            Packet::{variant}(val) => {{")
        bindings.append(f"                buffer.extend(&({i}u32).to_be_bytes());")
        bindings.append("                buffer.extend(&val.serialize());")
        bindings.append("            },")
    bindings.append("        }")
    bindings.append("        buffer")
    bindings.append("    }")
    bindings.append("")
    # Deserialization: read the first 4 bytes as command id then deserialize accordingly.
    bindings.append("    pub fn deserialize(data: &[u8]) -> Option<Packet> {")
    bindings.append("        if data.len() < 4 {")
    bindings.append("            return None;")
    bindings.append("        }")
    bindings.append("        let command_id = u32::from_be_bytes(data[0..4].try_into().ok()?);")
    bindings.append("        let payload = &data[4..];")
    bindings.append("        match command_id {")
    for i, table in enumerate(json_data["tables"]):
        variant = snake_to_camel(table["name"])
        bindings.append(f"            {i} => {{")
        bindings.append(f"                let val = {variant}::deserialize(payload)?;")
        bindings.append(f"                Some(Packet::{variant}(val))")
        bindings.append("            },")
    bindings.append("            _ => None,")
    bindings.append("        }")
    bindings.append("    }")
    bindings.append("}\n")
    
    return header + "\n".join(bindings)

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

def generate_sql_file(json_data: dict) -> str:
    code = "pub const DATABASE_SCHEMA: &str = r###\""
    for table in json_data["tables"]:
        code += generate_sql_schema(table)
        code += "\n"
    code += "\"###;\n\n"
    return code

def write_to_file(filename: str, content: str):
    output_dir = os.path.dirname(filename)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)

def main():
    args = sys.argv
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
            # Not implemented in this script (use your existing generate_bindings.py for cpp)
            print("C++ generation is not implemented in this script.")
            return
        elif lang == "rust":
            rust_code = generate_sql_file(json_data) + "\n\n" +  generate_rust_file(json_data)
            write_to_file(output_file, rust_code)

if __name__ == "__main__":
    main()
