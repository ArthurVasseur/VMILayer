use bindings::Packet;
use chrono::DateTime;
use r2d2::Pool;
use r2d2_sqlite::SqliteConnectionManager;
use rusqlite::params;
use std::sync::mpsc;
use std::thread;
use std::time::Duration;
use std::io::Read;
mod bindings;

fn init_database(pool: &Pool<SqliteConnectionManager>) {
    let conn = pool
        .get()
        .expect("Could not get a connection from the pool");
    conn.execute_batch(bindings::DATABASE_SCHEMA)
        .expect("Failed to create database schema");
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
fn main() {
    let now: DateTime<chrono::Utc> = chrono::Utc::now();
    let database_name = format!("{}.vmi", now.format("%Y-%m-%d_%H-%M-%S-%3f"));
    let vmi_temp_dir = std::env::temp_dir().join("VulkanMemoryInspector");
    std::fs::create_dir_all(&vmi_temp_dir).expect("Could not create directory");
    let database_path = vmi_temp_dir.join(database_name);
    let manager = SqliteConnectionManager::file(&database_path);
    let pool = Pool::new(manager).expect("Could not create a connection pool");

    init_database(&pool);
    println!("Database initialized at {}", database_path.display());

    let (tx, rx) = mpsc::channel::<bindings::Packet>();

    let socket_tx = tx.clone();
    thread::spawn(move || {
        let listener = std::net::TcpListener::bind("127.0.0.1:2104").unwrap();
        for stream in listener.incoming() {
            match stream {
                Ok(stream) => {
                    println!("New connection: {}", stream.peer_addr().unwrap());
                    let socket_tx_clone = socket_tx.clone();
                    thread::spawn(move || {
                            handle_client(stream, socket_tx_clone);
                    });
                }
                Err(err) => println!("Connection failed due to {:?}", err)
            }
        }
    });

    let pool_clone = pool.clone();
    thread::spawn(move || {
        let mut buffer: Vec<bindings::Packet> = Vec::new();

        loop {
            while let Ok(event) = rx.recv_timeout(Duration::from_millis(10)) {
                buffer.push(event);
                if buffer.len() >= 100 {
                    break;
                }
            }

            if !buffer.is_empty() {
                let mut conn = pool_clone
                    .get()
                    .expect("Impossible de récupérer une connexion du pool");
                let tx = conn
                    .transaction()
                    .expect("Échec du démarrage de la transaction");

                for event in &buffer {
                    match event {
                        Packet::VulkanEvent(vulkan_event) => {
                            tx.execute(
                                "INSERT INTO vulkan_event (timestamp, frame_number, function_name, parameters, result_code, thread_id)
                                VALUES (?1, ?2, ?3, ?4, ?5, ?6)",
                                params![
                                    vulkan_event.timestamp,
                                    vulkan_event.frame_number,
                                    vulkan_event.function_name,
                                    vulkan_event.parameters,
                                    vulkan_event.result_code,
                                    vulkan_event.thread_id,
                                ],
                            ).expect("Could not insert Vulkan event");
                        }
                        Packet::MemoryUsage(memory_usage_event) => {
                            tx.execute(
                                "INSERT INTO memory_usage (device_memory, frame_index_allocated, allocated_at, allocation_size, frame_index_deallocated, deallocated_at)
                                VALUES (?1, ?2, ?3, ?4, ?5, ?6)",
                                params![
                                    memory_usage_event.device_memory,
                                    memory_usage_event.frame_index_allocated,
                                    memory_usage_event.allocated_at,
                                    memory_usage_event.allocation_size,
                                    memory_usage_event.frame_index_deallocated,
                                    memory_usage_event.deallocated_at,
                                ],
                            ).expect("Could not insert Memory usage event");
                        }
                        Packet::FrameInformation(frame_information) => {
                            tx.execute(
                                "INSERT INTO frame_information (frame_index, started_at)
                                VALUES (?1, ?2)",
                                params![
                                    frame_information.frame_index,
                                    frame_information.started_at,
                                ],
                            ).expect("Could not insert Frame information event");
                        }
                    }
                }

                tx.commit().expect("Could not commit transaction");
                buffer.clear();
            }
        }
    });

    app_lib::run(&pool);
}


fn handle_client(mut stream: std::net::TcpStream, zmq_tx: mpsc::Sender<Packet>) {
    let mut buffer = [0; 4096];
    loop {
        match stream.read(&mut buffer) {
            Ok(0) => break, // Connection closed
            Ok(n) => {
                let packet = Packet::deserialize(&buffer[..n]);
                if packet.is_none() {
                    eprintln!("Failed to deserialize packet");
                    continue;
                }
                zmq_tx.send(packet.unwrap()).unwrap_or_else(|e| {
                    eprintln!("Failed to send packet to main thread: {}", e);
                });
            }
            Err(e) => {
                eprintln!("Error reading from stream: {}", e);
                break;
            }
        }
    }
}