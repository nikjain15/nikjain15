# nikjain15

GitHub profile repository. The single source of content is `README.md`, which renders on the profile page at github.com/nikjain15.

## Project overview
This repository hosts the profile README. It also holds one self-contained project, `pm_os/`, a fixed income SMA analyst agent with its own [AGENTS.md](pm_os/AGENTS.md), tests and setup.

## Structure
- `README.md`: the profile page content (hero, work, projects, track record, links).

## Setup, build, testing
The profile README has no build step. For `pm_os/`: `cd pm_os && pip install -e ".[ui,dev]" && pytest`.

## Conventions
- House style: senior, precise, positive. Use colons, commas, or periods instead of dashes as separators. Avoid em dashes.
- Keep links and figures accurate to the linked repositories.

## Commit and PR guidelines
- Edit `README.md`, open a PR to `main`, keep one concern per PR.
