use std::{env, path::Path};

fn main() {
    tauri_build::build();
    let out_dir = env::var("OUT_DIR").unwrap();
    let bindings_path = Path::new(&out_dir).join("bindings.rs");
    let output = std::process::Command::new("python.exe")
        .arg("../../../generate_bindings.py")
        .arg("rust")
        .arg(bindings_path)
        .output()
        .expect("Failed to generate bindings");
    println!("Bindings generation output: {:?}", output);
}
