use std::os::unix::process::CommandExt;
use std::process::Command;

fn main() {
    let args: Vec<String> = std::env::args().skip(1).collect();

    let err = Command::new("git").args(&args).exec();

    eprintln!("git-loco: failed to run git: {err}");
    std::process::exit(1);
}