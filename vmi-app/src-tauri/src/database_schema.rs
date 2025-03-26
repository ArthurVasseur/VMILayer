pub const DATABASE_SCHEMA: &str = r#"
-- Table for logging intercepted Vulkan events:
CREATE TABLE vulkan_events (
	id INTEGER PRIMARY KEY AUTOINCREMENT,
	timestamp TIMESTAMP NOT NULL,
	frame_number INTEGER NOT NULL,
	function_name TEXT NOT NULL,
	event_type TEXT,
	memory_delta BIGINT,
	parameters TEXT,
	result_code INTEGER,
	thread_id TEXT
);
CREATE TABLE frame_information (
	frame_index INTEGER PRIMARY KEY,
	started_at TIMESTAMP NOT NULL
);

-- Table for periodic memory usage snapshots:
CREATE TABLE memory_usage(
	id INTEGER PRIMARY KEY AUTOINCREMENT,
	device_memory BIGINT,
	frame_index_allocated INTEGER NOT NULL,
	allocated_at TIMESTAMP NOT NULL,
	allocation_size BIGINT,
	frame_index_deallocated INTEGER,
	deallocated_at TIMESTAMP
);
"#;