use std::{env, path::Path};

fn main() {
    tauri_build::build();
    let out_dir = env::var("OUT_DIR").unwrap();
    let bindings_path = Path::new(&out_dir).join("bindings.rs");
    let output = std::process::Command::new("python.exe")
        .arg("../../generate_bindings.py")
        .arg("rust")
        .arg(bindings_path)
        .arg("../../schema.json")
        .output()
        .expect("Failed to generate bindings");
    println!("cargo:rerun-if-changed={}", "../../generate_bindings.py");
    println!("cargo:rerun-if-changed={}", "../../schema.json");
}
