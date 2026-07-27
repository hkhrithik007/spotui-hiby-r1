use std::{
    env, fs,
    path::PathBuf,
    process::{ExitCode, exit},
};

use librespot_core::{
    authentication::Credentials, cache::Cache, config::SessionConfig, session::Session,
};
use librespot_oauth::OAuthClientBuilder;

const VERSION: &str = "0.1.0-beta.1";
const DEFAULT_PORT: u16 = 5588;
const CREDENTIALS_FILENAME: &str = "credentials.json";
const SUCCESS_PAGE: &str = r#"<!doctype html>
<html lang="en">
<head><meta charset="utf-8"><title>SpotUI authentication complete</title></head>
<body><h1>SpotUI authentication complete</h1><p>You may close this page and return to the installer.</p></body>
</html>"#;

struct Arguments {
    output_dir: PathBuf,
    port: u16,
    open_browser: bool,
}

fn usage(program: &str) {
    println!(
        "Usage: {program} --output-dir PATH [--port PORT] [--no-open]\n\
         \n\
         Opens Spotify's OAuth authorization page and writes a reusable\n\
         librespot credentials.json into PATH. The credential value is never\n\
         printed. PATH must not already contain credentials.json."
    );
}

fn parse_arguments() -> Result<Arguments, String> {
    let mut args = env::args();
    let program = args
        .next()
        .unwrap_or_else(|| "spotui-auth-helper".to_string());
    let mut output_dir = None;
    let mut port = DEFAULT_PORT;
    let mut open_browser = true;

    while let Some(argument) = args.next() {
        match argument.as_str() {
            "--output-dir" => {
                let value = args
                    .next()
                    .ok_or_else(|| "--output-dir requires a path".to_string())?;
                output_dir = Some(PathBuf::from(value));
            }
            "--port" => {
                let value = args
                    .next()
                    .ok_or_else(|| "--port requires a value".to_string())?;
                port = value
                    .parse::<u16>()
                    .map_err(|_| "--port must be an integer from 1 to 65535".to_string())?;
                if port == 0 {
                    return Err("--port must be an integer from 1 to 65535".to_string());
                }
            }
            "--no-open" => open_browser = false,
            "--version" => {
                println!("spotui-auth-helper {VERSION} (librespot 0.8.0)");
                exit(0);
            }
            "--help" | "-h" => {
                usage(&program);
                exit(0);
            }
            _ => return Err(format!("unknown argument: {argument}")),
        }
    }

    let output_dir = output_dir.ok_or_else(|| "--output-dir is required".to_string())?;

    Ok(Arguments {
        output_dir,
        port,
        open_browser,
    })
}

fn secure_path(path: &PathBuf, mode: u32) -> Result<(), String> {
    #[cfg(unix)]
    {
        use std::os::unix::fs::PermissionsExt;

        fs::set_permissions(path, fs::Permissions::from_mode(mode))
            .map_err(|error| format!("could not secure {}: {error}", path.display()))?;
    }

    #[cfg(not(unix))]
    let _ = (path, mode);

    Ok(())
}

async fn run(arguments: Arguments) -> Result<(), String> {
    if arguments.output_dir.exists() {
        let metadata = fs::symlink_metadata(&arguments.output_dir).map_err(|error| {
            format!(
                "could not inspect output directory {}: {error}",
                arguments.output_dir.display()
            )
        })?;
        if metadata.file_type().is_symlink() || !metadata.is_dir() {
            return Err("output path must be a private directory, not a symlink".to_string());
        }
        #[cfg(unix)]
        {
            use std::os::unix::fs::PermissionsExt;

            if metadata.permissions().mode() & 0o077 != 0 {
                return Err(
                    "existing output directory is accessible by other users; use mode 0700"
                        .to_string(),
                );
            }
        }
    } else {
        fs::create_dir_all(&arguments.output_dir).map_err(|error| {
            format!(
                "could not create output directory {}: {error}",
                arguments.output_dir.display()
            )
        })?;
        secure_path(&arguments.output_dir, 0o700)?;
    }

    let credentials_path = arguments.output_dir.join(CREDENTIALS_FILENAME);
    if credentials_path.exists() {
        return Err(format!(
            "refusing to overwrite existing {}",
            credentials_path.display()
        ));
    }

    let mut session_config = SessionConfig::default();
    session_config.tmp_dir = arguments.output_dir.join("tmp");
    fs::create_dir_all(&session_config.tmp_dir)
        .map_err(|error| format!("could not create private session temp directory: {error}"))?;
    secure_path(&session_config.tmp_dir, 0o700)?;
    let redirect_uri = format!("http://127.0.0.1:{}/login", arguments.port);
    let scopes = vec![
        "streaming",
        "user-library-read",
        "playlist-read-private",
        "playlist-read-collaborative",
    ];
    let mut oauth_builder = OAuthClientBuilder::new(
        &session_config.client_id,
        &redirect_uri,
        scopes,
    )
    .with_custom_message(SUCCESS_PAGE);
    if arguments.open_browser {
        oauth_builder = oauth_builder.open_in_browser();
    }
    let oauth_client = oauth_builder
        .build()
        .map_err(|error| format!("could not prepare Spotify OAuth: {error}"))?;

    println!("Authorize SpotUI in the browser window.");
    println!("If it does not open, copy the Browse to URL shown below.");
    let token = oauth_client
        .get_access_token()
        .map_err(|error| format!("Spotify OAuth failed: {error}"))?;

    let no_audio_cache: Option<&PathBuf> = None;
    let cache = Cache::new(
        Some(&arguments.output_dir),
        Some(&arguments.output_dir),
        no_audio_cache,
        None,
    )
    .map_err(|error| format!("could not prepare the private credential cache: {error}"))?;
    let session = Session::new(session_config, Some(cache));

    println!("Authorization received; creating the reusable device credential.");
    session
        .connect(Credentials::with_access_token(token.access_token), true)
        .await
        .map_err(|error| format!("Spotify session authentication failed: {error}"))?;
    session.shutdown();

    let metadata = fs::metadata(&credentials_path).map_err(|error| {
        format!(
            "librespot did not create {}: {error}",
            credentials_path.display()
        )
    })?;
    if !metadata.is_file() || metadata.len() == 0 {
        return Err("librespot created an invalid empty credential file".to_string());
    }
    secure_path(&credentials_path, 0o600)?;

    println!("Authentication complete; reusable credentials created privately.");
    Ok(())
}

#[tokio::main(flavor = "current_thread")]
async fn main() -> ExitCode {
    let arguments = match parse_arguments() {
        Ok(arguments) => arguments,
        Err(error) => {
            eprintln!("error: {error}");
            eprintln!("Run with --help for usage.");
            return ExitCode::from(2);
        }
    };

    match run(arguments).await {
        Ok(()) => ExitCode::SUCCESS,
        Err(error) => {
            eprintln!("error: {error}");
            ExitCode::FAILURE
        }
    }
}
