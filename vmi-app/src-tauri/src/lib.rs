use std::collections::HashMap;
use std::{fs, io};
use std::path::{Path, PathBuf};
use std::process;

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_dialog::init())
        .setup(|app| {
            if cfg!(debug_assertions) {
                app.handle().plugin(
                    tauri_plugin_log::Builder::default()
                        .level(log::LevelFilter::Info)
                        .build(),
                )?;
            }
            Ok(())
        })
        .invoke_handler(tauri::generate_handler!(launch_application))
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}

#[tauri::command]
fn launch_application(file_path: String, working_directory: String, command_args: String) {
    let file_path = PathBuf::from(file_path);
    let working_directory = PathBuf::from(working_directory);
    let command_args = command_args
        .split_whitespace()
        .map(String::from)
        .collect::<Vec<String>>();

    let mut env = HashMap::new();

    let layer_path = PathBuf::from("../../vmi-layer/VK_LAYER_vmi.json");
    let layer_full_path = fs::canonicalize(&layer_path).unwrap_or_else(|error| {
        panic!("Failed to get the full path of the layer file: {:?}, error: {:?}", layer_path, error)
    });

    env.insert(
        "VK_ADD_IMPLICIT_LAYER_PATH".into(),
        layer_full_path.to_str().unwrap_or("").into(),
    );
    env.insert("VK_LAYERS_ALLOW_ENV_VAR".into(), "1".into());
    env.insert("VK_INSTANCE_LAYERS".into(), "VK_LAYER_AV_vmi".into());
    env.insert("VK_LOADER_LAYERS_ENABLE".into(), "VK_LAYER_AV_vmi".into());
    env.insert("ENABLE_VMI_LAYER".into(), "1".into());
    //env.insert("VK_LOADER_DEBUG".into(), "all".into());

    match spawn_detached_process(file_path.as_path(), &command_args, &working_directory, &env) {
        Ok(_) => println!(
            "Successfully launched application with file path: {}",
            file_path.display()
        ),
        Err(e) => {
            eprintln!("Error launching application: {}", e)
        }
    }
}

#[cfg(windows)]
fn spawn_detached_process(
    program_path: &Path,
    program_args: &[String],
    program_cwd: &Path,
    program_env: &HashMap<String, String>,
) -> io::Result<process::Child> {
    use std::os::windows::process::CommandExt;

    const CREATE_NEW_PROCESS_GROUP: u32 = 0x00000200;
    const DETACHED_PROCESS: u32 = 0x00000008;

    process::Command::new(program_path)
        .creation_flags(CREATE_NEW_PROCESS_GROUP | DETACHED_PROCESS)
        .args(program_args)
        .current_dir(program_cwd)
        .envs(program_env)
        .spawn()
}

#[cfg(not(windows))]
fn spawn_detached_process(
    program_path: &Path,
    program_args: &[String],
    program_cwd: &Path,
    program_env: &HashMap<String, String>,
) -> io::Result<process::Child> {
    process::Command::new(program_path)
        .args(program_args)
        .current_dir(program_cwd)
        .envs(program_env)
        .spawn()
}
