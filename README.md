# git-loco

Record where you make Git commits!

git-loco captures your location and commit metadata, stores it locally in SQLite, and optionally syncs to Cloudflare D1.

## Requirements

- Python 3.11+
- [uv](https://docs.astral.sh/uv/getting-started/installation/)
- Git
- Windows or WSL, with Windows location services enabled (only tested on WSL)

## Install

Clone the project, then run this inside the project folder:

```sh
uv tool install .
```

## Usage

Run this inside a Git repository for which you want to capture commit locations:

```sh
git-loco hook install
```

This installs a Git `post-commit` hook in that repository. After each commit, the hook runs `git-loco capture` to save your current location and commit metadata locally.

Capture is enabled per repository, and other repositories are not affected.

To capture the latest commit manually:

```sh
git-loco capture
```

To remove the hook and stop automatic capture in a repository:

```sh
git-loco hook uninstall
```

## Optional: Sync to Cloudflare D1

1. Create a [Cloudflare D1 database](https://developers.cloudflare.com/d1/get-started/).
2. Run the `config set` command and enter your API token, account ID, and database ID when prompted:

   ```sh
   git-loco config set d1
   ```

3. Sync your captured records:

   ```sh
   git-loco sync d1
   ```

Sync creates the required tables automatically.

## Privacy

Captured data includes location coordinates, commit messages, author names and emails, and local repository paths.

Data stays in a local `loco.db` file in your user data directory unless you run `sync`. Sync uploads captured records across repositories to the configured provider.

Disabling the hook stops automatic capture. It does not delete existing records.
