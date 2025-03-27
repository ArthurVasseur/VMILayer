use std::sync::mpsc;
use std::thread;
use std::time::Duration;
use chrono::DateTime;
use r2d2::Pool;
use r2d2_sqlite::SqliteConnectionManager;
use rusqlite::params;
use zmq;
use serde::Deserialize;
mod bindings;

fn init_database(pool: &Pool<SqliteConnectionManager>) {
    let conn = pool.get().expect("Could not get a connection from the pool");
    conn.execute_batch(bindings::DATABASE_SCHEMA).expect("Failed to create database schema");
}

fn main() {
    let now: DateTime<chrono::Utc> = chrono::Utc::now();
    let database_name = format!("{}.vmi", now.format("%Y-%m-%d_%H-%M-%S-%3f"));
    let vmi_temp_dir = std::env::temp_dir().join("VulkanMemoryInspector");
    std::fs::create_dir_all(&vmi_temp_dir).expect("Could not create directory");
    let database_path  = vmi_temp_dir.join(database_name);
    let manager = SqliteConnectionManager::file(&database_path);
    let pool = Pool::new(manager).expect("Could not create a connection pool");

    init_database(&pool);
    println!("Database initialized at {}", database_path.display());

    let (tx, rx) = mpsc::channel::<bindings::VulkanEvent>();

    let zmq_tx = tx.clone();
    thread::spawn(move || {
        let context = zmq::Context::new();
        let socket = context.socket(zmq::REP).expect("Impossible de créer le socket ZMQ");
        socket.bind("tcp://*:2104").expect("Échec du bind du socket ZMQ");

        loop {
            let msg = match socket.recv_msg(0) {
                Ok(m) => m,
                Err(e) => {
                    eprintln!("Erreur lors de la réception ZMQ: {}", e);
                    continue;
                }
            };

            let msg_str = msg.as_str().unwrap_or("");
            println!("Message reçu: {}", msg_str);

            let event: bindings::VulkanEvent = match serde_json::from_str(msg_str) {
                Ok(ev) => ev,
                Err(e) => {
                    eprintln!("Erreur de parsing JSON: {}", e);
                    continue;
                }
            };

            if let Err(e) = zmq_tx.send(event) {
                eprintln!("Erreur lors de l'envoi de l'événement: {}", e);
            }

            socket.send("Accusé de réception", 0).expect("Échec de l'envoi de la réponse ZMQ");
        }
    });

    let pool_clone = pool.clone();
    thread::spawn(move || {
        let mut buffer: Vec<bindings::VulkanEvent> = Vec::new();

        loop {
            while let Ok(event) = rx.recv_timeout(Duration::from_millis(100)) {
                buffer.push(event);
                if buffer.len() >= 100 {
                    break;
                }
            }

            if !buffer.is_empty() {
                let mut conn = pool_clone.get().expect("Impossible de récupérer une connexion du pool");
                let tx = conn.transaction().expect("Échec du démarrage de la transaction");

                for event in &buffer {
                    tx.execute(
                        "INSERT INTO vulkan_events (timestamp, frame_number, function_name, event_type, memory_delta, parameters, result_code, thread_id)
                        VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8)",
                        params![
                            event.timestamp,
                            event.frame_number,
                            event.function_name,
                            event.event_type,
                            event.memory_delta,
                            event.parameters,
                            event.result_code,
                            event.thread_id,
                        ],
                    ).expect("Could not insert Vulkan event");
                }

                tx.commit().expect("Could not commit transaction");
                println!("Inserted {} in one batch", buffer.len());
                buffer.clear();
            }
        }
    });

    app_lib::run();
}
