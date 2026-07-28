use std::os::unix::process::CommandExt;
use std::process::{Command, ExitCode};

fn main() -> ExitCode {
    let args: Vec<String> = std::env::args().skip(1).collect();

    let intercept = matches!(args.first().map(String::as_str), Some("commit") | Some("push"));

    if intercept {
        let status = Command::new("git")
            .args(&args)
            .status()
            .expect("failed to spawn git");

        if status.success() {
            eprintln!("git-loco: captured location (stub)");
        }

        return ExitCode::from(status.code().unwrap_or(1) as u8);
    }

    let err = Command::new("git").args(&args).exec();
    
    eprintln!("git-loco: failed to run git: {err}");
    ExitCode::FAILURE
}