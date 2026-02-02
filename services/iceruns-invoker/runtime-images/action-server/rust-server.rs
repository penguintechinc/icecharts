// Action container server for Rust runtime (OpenWhisk /init and /run pattern)

use std::net::TcpListener;

fn main() {
    let listener = TcpListener::bind("0.0.0.0:8080").unwrap();
    println!("Action server listening on port 8080");

    for stream in listener.incoming() {
        match stream {
            Ok(_stream) => {
                // Handle request (stub)
                println!("Connection received");
            }
            Err(e) => {
                eprintln!("Error: {}", e);
            }
        }
    }
}
