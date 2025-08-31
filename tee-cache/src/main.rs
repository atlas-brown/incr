use std::io::{self, Read, Write};
use std::fs::File;
use std::path::Path;
use std::env;

#[derive(Debug)]
enum OutputStatus {
    Completed,
    StdoutError(String),
    StdinError(String),
}

fn main() -> io::Result<()> {
    // Get file identifier from command line arguments
    let file_id = match env::args().nth(1) {
        Some(id) => id,
        None => {
            eprintln!("Error: No file identifier provided");
            eprintln!("Usage: {} <file_identifier>", env::args().next().unwrap());
            std::process::exit(1);
        }
    };

    // Create temp file with the provided identifier
    let temp_dir = std::env::temp_dir();
    let temp_filename = format!("cache_{}.tmp", file_id);
    let temp_path = temp_dir.join(&temp_filename);
    
    let mut temp_file = File::create(&temp_path)?;
    // eprintln!("Caching intermediate results to: {}", temp_path.display());

    // Buffer for reading from stdin
    let mut buffer = [0; 8192];
    let mut stdin = io::stdin();
    let mut stdout = io::stdout();
    
    let mut status = OutputStatus::Completed;
    let mut stdin_closed_normally = false;

    loop {
        // Read from stdin
        match stdin.read(&mut buffer) {
            Ok(0) => {
                // EOF reached - normal termination
                stdin_closed_normally = true;
                break;
            }
            Ok(n) => {
                // Successfully read data
                let data = &buffer[..n];
                
                // Always write to temp file
                if let Err(e) = temp_file.write_all(data) {
                    status = OutputStatus::StdinError(format!("Temp file write error: {}", e));
                    break;
                }
                
                // Try to write to stdout, but continue if it fails
                match stdout.write_all(data) {
                    Ok(_) => {
                        if let Err(e) = stdout.flush() {
                            status = OutputStatus::StdoutError(format!("Stdout flush error: {}", e));
                            // Continue writing to temp file despite stdout error
                        }
                    }
                    Err(e) => {
                        status = OutputStatus::StdoutError(format!("Stdout write error: {}", e));
                        // Continue writing to temp file despite stdout error
                    }
                }
            }
            Err(e) => {
                // Error reading from stdin
                status = OutputStatus::StdinError(format!("Stdin read error: {}", e));
                break;
            }
        }
    }

    // Ensure all data is flushed to temp file
    if let Err(e) = temp_file.sync_all() {
        eprintln!("Warning: failed to sync temp file: {}", e);
    }

    // Write status file
    let status_filename = format!("status_{}.txt", file_id);
    let status_path = temp_dir.join(&status_filename);
    write_status_file(&status_path, &status, stdin_closed_normally)?;

    // eprintln!("Operation completed. Status: {:?}", status);
    // eprintln!("Temp file: {}", temp_path.display());
    // eprintln!("Status file: {}", status_path.display());

    Ok(())
}

fn write_status_file(path: &Path, status: &OutputStatus, stdin_closed_normally: bool) -> io::Result<()> {
    let mut status_file = File::create(path)?;
    
    let status_line = match status {
        OutputStatus::Completed => {
            if stdin_closed_normally {
                "STATUS: COMPLETED\nSTDIN: CLOSED_NORMALLY\nSTDOUT: OK".to_string()
            } else {
                "STATUS: COMPLETED\nSTDIN: INTERRUPTED\nSTDOUT: OK".to_string()
            }
        }
        OutputStatus::StdoutError(error) => {
            if stdin_closed_normally {
                format!("STATUS: PARTIAL_SUCCESS\nSTDIN: CLOSED_NORMALLY\nSTDOUT: ERROR\nERROR: {}", error)
            } else {
                format!("STATUS: PARTIAL_SUCCESS\nSTDIN: INTERRUPTED\nSTDOUT: ERROR\nERROR: {}", error)
            }
        }
        OutputStatus::StdinError(error) => {
            format!("STATUS: ERROR\nSTDIN: ERROR\nSTDOUT: UNKNOWN\nERROR: {}", error)
        }
    };

    writeln!(status_file, "{}", status_line)?;
    status_file.sync_all()?;
    
    Ok(())
}