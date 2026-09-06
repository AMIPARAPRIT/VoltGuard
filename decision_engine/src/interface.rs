use std::env;
use std::io::{self, Read};

pub fn read_input() -> String {
    let args: Vec<String> = env::args().collect();
    
    // Check if --json <json_string> argument is provided
    for i in 1..args.len() {
        if args[i] == "--json" && i + 1 < args.len() {
            return args[i + 1].clone();
        }
        if args[i] == "--help" || args[i] == "-h" {
            eprintln!("VoltGuard Decision Engine CLI\nUsage: decision_engine [--json '<json_payload>'] or pipe JSON via stdin");
            std::process::exit(0);
        }
    }

    // Check positional argument e.g. decision_engine input.json or direct inline json
    if args.len() > 1 && !args[1].starts_with('-') {
        let path_or_json = &args[1];
        if std::path::Path::new(path_or_json).is_file() {
            if let Ok(content) = std::fs::read_to_string(path_or_json) {
                return content;
            }
        }
        return path_or_json.clone();
    }

    // Fallback: Read from stdin
    let mut buffer = String::new();
    if io::stdin().read_to_string(&mut buffer).is_ok() && !buffer.trim().is_empty() {
        return buffer;
    }

    buffer
}
