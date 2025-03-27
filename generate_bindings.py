#!/usr/bin/env python3
import json
import os

# Chargement des données JSON depuis le fichier "schema.json"
with open("schema.json", "r", encoding="utf-8") as f:
    json_data = json.load(f)

# Table de correspondance entre les types JSON et les types dans chaque langage
type_mapping = {
    "i32": {"cpp": "int32_t", "rust": "i32", "sql": "INTEGER"},
    "i64": {"cpp": "int64_t", "rust": "i64", "sql": "BIGINT"},
    "str": {"cpp": "std::string", "rust": "String", "sql": "TEXT"}
}

# Conversion d'un nom en snake_case vers CamelCase (pour le nom de classe en C++)
def snake_to_camel(name: str) -> str:
    return "".join(word.capitalize() for word in name.split('_'))

# Pour les membres de C++ on transforme le snake_case en camelCase (première lettre en minuscule)
def snake_to_field(name: str) -> str:
    parts = name.split('_')
    return parts[0].lower() + "".join(word.capitalize() for word in parts[1:])

# Génération du binding C++ avec implémentation complète
def generate_cpp_binding(table: dict) -> str:
    class_name = snake_to_camel(table["name"])
    code = []
    code.append(f"class {class_name} {{")
    code.append("public:")
    # Déclaration des membres
    for col in table["columns"]:
        cpp_type = type_mapping[col["type"]]["cpp"]
        field_name = snake_to_field(col["name"])
        code.append(f"\t{cpp_type} {field_name};")
    code.append("")
    # Fonction serialize()
    code.append("\tstd::vector<uint8_t> serialize() const {")
    code.append("\t\tsize_t total_size = 0;")
    # Calcul de la taille totale
    for col in table["columns"]:
        field_name = snake_to_field(col["name"])
        if col["type"] == "str":
            code.append(f"\t\ttotal_size += sizeof(uint32_t) + {field_name}.size();")
        else:
            cpp_type = type_mapping[col["type"]]["cpp"]
            code.append(f"\t\ttotal_size += sizeof({cpp_type});")
    code.append("\t\tstd::vector<uint8_t> buffer(total_size);")
    code.append("\t\tsize_t offset = 0;")
    # Sérialisation de chaque champ
    for col in table["columns"]:
        cpp_type = type_mapping[col["type"]]["cpp"]
        field_name = snake_to_field(col["name"])
        if col["type"] == "str":
            code.append(f'\t\t// Sérialisation de {field_name} (string)')
            code.append(f'\t\tuint32_t len_{field_name} = static_cast<uint32_t>({field_name}.size());')
            code.append(f'\t\tlen_{field_name} = Concerto::ByteSwap::Swap(len_{field_name});')
            code.append(f'\t\tstd::memcpy(buffer.data() + offset, &len_{field_name}, sizeof(uint32_t));')
            code.append(f'\t\toffset += sizeof(uint32_t);')
            code.append(f'\t\tstd::memcpy(buffer.data() + offset, {field_name}.data(), {field_name}.size());')
            code.append(f'\t\toffset += {field_name}.size();')
        else:
            code.append(f'\t\t// Sérialisation de {field_name} (numeric)')
            code.append(f'\t\t{cpp_type} temp_{field_name} = Concerto::ByteSwap::Swap({field_name});')
            code.append(f'\t\tstd::memcpy(buffer.data() + offset, &temp_{field_name}, sizeof({cpp_type}));')
            code.append(f'\t\toffset += sizeof({cpp_type});')
    code.append("\t\treturn buffer;")
    code.append("\t}")
    code.append("")
    # Fonction deserialize()
    code.append(f'\tstatic {class_name} deserialize(const std::vector<uint8_t>& buffer) {{')
    code.append(f'\t\t{class_name} obj;')
    code.append("\t\tsize_t offset = 0;")
    for col in table["columns"]:
        cpp_type = type_mapping[col["type"]]["cpp"]
        field_name = snake_to_field(col["name"])
        if col["type"] == "str":
            code.append(f'\t\t// Désérialisation de {field_name} (string)')
            code.append(f'\t\tuint32_t len_{field_name};')
            code.append(f'\t\tstd::memcpy(&len_{field_name}, buffer.data() + offset, sizeof(uint32_t));')
            code.append(f'\t\tlen_{field_name} = Concerto::ByteSwap::Swap(len_{field_name});')
            code.append(f'\t\toffset += sizeof(uint32_t);')
            code.append(f'\t\tobj.{field_name}.assign(reinterpret_cast<const char*>(buffer.data() + offset), len_{field_name});')
            code.append(f'\t\toffset += len_{field_name};')
        else:
            code.append(f'\t\t// Désérialisation de {field_name} (numeric)')
            code.append(f'\t\t{cpp_type} temp_{field_name};')
            code.append(f'\t\tstd::memcpy(&temp_{field_name}, buffer.data() + offset, sizeof({cpp_type}));')
            code.append(f'\t\tobj.{field_name} = Concerto::ByteSwap::Swap(temp_{field_name});')
            code.append(f'\t\toffset += sizeof({cpp_type});')
    code.append("\t\treturn obj;")
    code.append("\t}")
    code.append("};")
    return "\n".join(code)

# Génération du binding Rust (version simplifiée)
def generate_rust_binding(table: dict) -> str:
    struct_name = snake_to_camel(table["name"])
    lines = []
    lines.append("#[derive(Debug)]")
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

# Génération du schéma SQL
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

# Fonction pour écrire dans un fichier
def write_to_file(filename: str, content: str):
    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)

# Génération du fichier C++ complet
def generate_cpp_file(json_data: dict) -> str:
    header = (
        "#include <cstdint>\n"
        "#include <vector>\n"
        "#include <string>\n"
        "#include <cstring>\n"
        "#include \"Concerto/Core/ByteSwap.hpp\"\n\n"
    )
    classes = []
    for table in json_data["tables"]:
        classes.append(generate_cpp_binding(table))
        classes.append("\n")
    return header + "\n".join(classes)

# Génération du fichier Rust
def generate_rust_file(json_data: dict) -> str:
    modules = []
    for table in json_data["tables"]:
        modules.append(generate_rust_binding(table))
        modules.append("\n")
    return "\n".join(modules)

# Génération du fichier SQL
def generate_sql_file(json_data: dict) -> str:
    statements = []
    for table in json_data["tables"]:
        statements.append(generate_sql_schema(table))
        statements.append("\n")
    return "\n".join(statements)

def main():
    args = os.sys.argv
    if len(args) != 3:
        print("Usage: python generate_bindings.py lang output_file")
        return
    
    lang = args[1]
    output_file = args[2]
    if lang not in ["cpp", "rust", "sql"]:
        print("Invalid language")
        return
    
    if lang == "cpp":
        content = generate_cpp_file(json_data)
        write_to_file(output_file, content)
    elif lang == "rust":
        content = generate_rust_file(json_data)
        write_to_file(output_file, content)
    else:
        content = generate_sql_file(json_data)
        write_to_file(output_file, content)

if __name__ == "__main__":
    main()
