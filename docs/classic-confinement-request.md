# Classic-confinement request: `herdr` (not yet filed)

Template: <https://forum.snapcraft.io/t/about-the-classic-confinement-category/43830>.
Prior rejection this request must account for:
<https://forum.snapcraft.io/t/classic-confinement-request-herdr/52894>
(2026-08-26, rejected 2026-08-28 on publisher-vetting grounds only).

**Do not post this. Do not run `snapcraft register` or `snapcraft login`.**
Filing is conditional on `docs/upstream-adoption.md` producing a written
endorsement from herdrdev — see `upstream-relation` below, which stays an
open `TODO` until that happens.

---

- **name**: `herdr`

- **description**: Herdr is a terminal multiplexer built for coding agents.
  It keeps terminals running in a background server when you close the
  client or lose your SSH connection, marks every pane working, blocked or
  idle, and gathers local work and saved SSH machines into one window. This
  snap repacks the official upstream release binary for each architecture,
  verified against the sha256 published at `https://herdr.dev/latest.json`.

- **snapcraft**: permalink to this repository's `snap/snapcraft.yaml`, e.g.
  `https://github.com/canonicalayush/herdr-snap/blob/main/snap/snapcraft.yaml`
  once merged (replace with the exact commit permalink when filing).

- **upstream**: <https://github.com/herdrdev/herdr>

- **upstream-relation**: `TODO: requires upstream adoption — see
  https://forum.snapcraft.io/t/classic-confinement-request-herdr/52894`.
  Do not fill this in speculatively. The only acceptable content here is a
  link to a GitHub Discussion, repo README change, or email reply in which
  herdrdev names this packaging (or its maintainer) as official, matching
  one of the three models proposed in `docs/upstream-adoption.md`.

- **supported-category**: this snap fits three of the categories listed at
  <https://snapcraft.io/docs/reference/administration/reviewing-classic-confinement-snaps/#supported>
  simultaneously:
  - *Terminal emulators, multiplexers and shells* — herdr's entire purpose.
  - *Tools for local, non-root user driven configuration of/switching to
    development workspaces/environments* — `herdr workspace`/`herdr worktree`
    manage per-project dev environments and git worktrees across local and
    saved SSH machines.
  - *AI agent/assistant that runs arbitrary user-directed code and needs to
    reach files and programs that aren't known at build time* — herdr's
    reason for existing is running coding agents (Claude Code, Codex, etc.)
    against repositories chosen at runtime.

- **reasoning**: verified against upstream `master` (commit `ee5bfb5`):

  | herdr behaviour | Evidence | Strict-confinement verdict |
  |---|---|---|
  | Execs arbitrary host binaries in PTYs (`claude`, `codex`, user shell) | `src/` contains `Command::new("sh")` ×14, `Command::new("git")` ×14, `Command::new("ssh")` ×4, `Command::new("xdg-open")` | AppArmor denies exec of host paths; no interface grants it |
  | Opens repos anywhere on disk | pane cwd is user-chosen at runtime | the `home` interface covers only non-hidden `$HOME`; `personal-files`/`system-files` are super-privileged and are not granted for "anywhere" |
  | Its own state lives in `~/.herdr`/`~/.config/herdr` (present on this host); API socket defaults to the config dir | `HERDR_HOME`; `src/api/server.rs:1226` | the `home` interface's AppArmor policy excludes top-level dotfiles |
  | Shells out to `curl` for update manifests | `src/update.rs:336` calls `crate::noninteractive_process::curl_command()` | host binary, not shipped with the snap |
  | SSH to saved machines with the user's `~/.ssh` | `src/remote/attach.rs` | `ssh-keys` is privileged and still does not permit exec'ing a host `ssh` binary |
  | Runs user plugins | `HERDR_PLUGIN_ROOT`, `HERDR_PLUGIN_ENTRYPOINT_ID` | arbitrary exec again, target chosen by the user at runtime |

  No combination of supported strict-confinement interfaces permits
  exec'ing an arbitrary host binary chosen at runtime, which is what every
  row above reduces to. `home` excludes dotfiles (herdr's own state and the
  user's `.ssh`), and the privileged file-access interfaces
  (`personal-files`, `system-files`) are scoped allowlists, not an "anywhere
  on disk" grant — they do not fit a tool whose entire purpose is opening a
  cwd chosen interactively, with no fixed set of paths to declare.

  `snappy-debug` was not run: it surfaces interface *denials* that occurred
  at runtime, which presupposes a strict-confinement build to run it
  against. The blocker here is exec-of-arbitrary-host-binaries, a capability
  no strict-confinement interface grants regardless of which combination is
  requested, so there is no strict build for `snappy-debug` to instrument.

- [x] I understand that strict confinement is generally preferred over classic.
- [x] I've tried the [existing interfaces](https://snapcraft.io/docs/supported-interfaces)
      to make the snap work under strict confinement — see the `reasoning`
      table above for why `home`, `personal-files`, `system-files`, and
      `ssh-keys` each fall short of what herdr needs.
