use std::os::unix::process::CommandExt;
use std::process::{Command, ExitCode};
use std::time::Duration;

use zbus::blocking::Connection;

fn main() -> ExitCode {
    let args: Vec<String> = std::env::args().skip(1).collect();

    let intercept = args.iter().any(|a| a == "commit" || a == "push");

    if intercept {
        let status = Command::new("git")
            .args(&args)
            .status()
            .expect("failed to spawn git");

        if status.success() {
            match get_location() {
                Ok((lat, lon, accuracy)) => {
                    eprintln!(
                        "git-loco: location captured: {:.6}, {:.6} (±{:.0}m)",
                        lat, lon, accuracy
                    );
                }
                Err(e) => {
                    eprintln!("git-loco: location unavailable: {e}");
                }
            }
        }

        return ExitCode::from(status.code().unwrap_or(1) as u8);
    }

    let err = Command::new("git").args(&args).exec();

    eprintln!("git-loco: failed to run git: {err}");
    ExitCode::FAILURE
}

fn get_location() -> Result<(f64, f64, f64), Box<dyn std::error::Error>> {
    let conn = Connection::system()?;

    // Request a GeoClue client
    let reply = conn.call_method(
        Some("org.freedesktop.GeoClue2"),
        "/org/freedesktop/GeoClue2/Manager",
        Some("org.freedesktop.GeoClue2.Manager"),
        "GetClient",
        &(),
    )?;

    let body = reply.body();
    // GetClient returns (client_path)
    let client_path = body.deserialize::<zbus::zvariant::ObjectPath>()?;

    // Set DesiredAccuracy to 4 (street-level, ~neighborhood)
    // Levels: 0=none, 1=country, 2=city, 3=neighborhood, 4=street, 5=exact
    conn.call_method(
        Some("org.freedesktop.GeoClue2"),
        client_path.as_str(),
        Some("org.freedesktop.DBus.Properties"),
        "Set",
        &(
            "org.freedesktop.GeoClue2.Client",
            "DesiredAccuracy",
            zbus::zvariant::Value::U32(4),
        ),
    )?;

    // Start the client (triggers location lookup)
    conn.call_method(
        Some("org.freedesktop.GeoClue2"),
        client_path.as_str(),
        Some("org.freedesktop.GeoClue2.Client"),
        "Start",
        &(),
    )?;

    // Wait briefly for a location fix (WiFi positioning is fast, ~1-3s)
    std::thread::sleep(Duration::from_secs(3));

    // Read the Location property — returns an object path to a Location object
    let reply = conn.call_method(
        Some("org.freedesktop.GeoClue2"),
        client_path.as_str(),
        Some("org.freedesktop.DBus.Properties"),
        "Get",
        &("org.freedesktop.GeoClue2.Client", "Location"),
    )?;

    let body = reply.body();
    let location_path = body.deserialize::<zbus::zvariant::ObjectPath>()?;

    if location_path.as_str() == "/" {
        // No location available (root path = unset)
        conn.call_method(
            Some("org.freedesktop.GeoClue2"),
            client_path.as_str(),
            Some("org.freedesktop.GeoClue2.Client"),
            "Stop",
            &(),
        )?;
        return Err("no location fix available".into());
    }

    // Read latitude, longitude, accuracy from the Location object
    let latitude = get_double_property(&conn, location_path.as_str(), "Latitude")?;
    let longitude = get_double_property(&conn, location_path.as_str(), "Longitude")?;
    let accuracy = get_double_property(&conn, location_path.as_str(), "Accuracy")?;

    // Stop the client
    conn.call_method(
        Some("org.freedesktop.GeoClue2"),
        client_path.as_str(),
        Some("org.freedesktop.GeoClue2.Client"),
        "Stop",
        &(),
    )?;

    Ok((latitude, longitude, accuracy))
}

fn get_double_property(
    conn: &Connection,
    path: &str,
    property: &str,
) -> Result<f64, Box<dyn std::error::Error>> {
    let reply = conn.call_method(
        Some("org.freedesktop.GeoClue2"),
        path,
        Some("org.freedesktop.DBus.Properties"),
        "Get",
        &("org.freedesktop.GeoClue2.Location", property),
    )?;

    let body = reply.body();
    let value: zbus::zvariant::Value<'_> = body.deserialize()?;
    match value {
        zbus::zvariant::Value::F64(v) => Ok(v.into()),
        _ => Err(format!("unexpected type for {property}").into()),
    }
}
