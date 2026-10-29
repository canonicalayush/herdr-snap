# Asking herdrdev to adopt official snap packaging

Status: drafted, not posted. This is the canonical text for a GitHub Discussion
on `herdrdev/herdr` (category: Ideas) and an email to `hey@herdr.dev`. Posting
and sending are deliberately left to a human — see the note at the end of this
file.

## 1. What changed since the August request

On 2026-08-26, @leko filed a classic-confinement request for the `herdr` snap
name: <https://forum.snapcraft.io/t/classic-confinement-request-herdr/52894>.
On 2026-08-28, Snap Store reviewer Elise Hlady rejected it on one ground only:

> "due to the sensitive nature of classic confinement, publisher vetting is
> required, and this in turn requires the publisher to be an owner or snap
> maintainer of the upstream project. As such, the `herdr` snap does not
> currently meet our criteria and should not be granted classic confinement
> at this time. … I … encourage you to submit another request for classic if
> the upstream chooses to officially adopt this snap."

Category fit was never in question — the review raised no objection to
herdr's use case. The only blocker is publisher vetting, and the reviewer
named the exact fix: upstream adoption. That makes Snap Store distribution
for `herdr` a decision herdrdev can make unilaterally, with no further
negotiation needed on Canonical's side.

A similar discussion was opened in August and did not lead to adoption. This
is not a repeat of that ask — it is the same ask with the missing piece
Canonical supplied since then: a specific, written condition for approval.

## 2. Three ways to do this

herdr already has one officially-adopted-but-externally-maintained package: the
Nix flake at `herdrdev/herdr-nix`, which `release.yml` dispatches on each
release. Snap packaging fits the same pattern. In order of how much upstream
has to own:

1. **Packaging inside `herdrdev/herdr`** — a `snap/` directory in this repo,
   released the same way the existing Linux/macOS/Windows assets are.
2. **A `herdrdev/herdr-snap` repo** — mirrors the `herdrdev/herdr-nix`
   arrangement exactly: a separate repo, dispatched from `release.yml`,
   named and owned by herdrdev.
3. **An external repo upstream simply names as official** — lowest lift for
   herdrdev: a README link and a line in `release.yml`'s notes, nothing else
   to maintain.

I'll maintain the packaging under any of the three, for as long as upstream
wants that.

## 3. What already exists and what it proves

<https://github.com/canonicalayush/herdr-snap> is a working classic-snap
packaging of the current stable release, repacking the published Linux
binaries (not a source rebuild) with sha256 verification against
`https://herdr.dev/latest.json`. It:

- builds and installs via `sudo snap install --classic --dangerous ./herdr_*.snap`,
  verified end-to-end in a clean VM: version match, environment-scrub (no
  `SNAP_*` variables reach pane children), full `PATH` fidelity for
  user-installed tools, working git/ssh/shell exec from panes, and refusal of
  `herdr update`/`herdr channel set` in favor of `sudo snap refresh herdr`;
- runs the same checks in CI on every pull request and push to `main`;
- tracks new upstream releases with a Renovate PR roughly twice a month,
  checksums auto-filled by a follow-up workflow, every bump human-reviewed
  before merge.

It registers no name in the Snap Store, uploads nothing, and holds no store
credentials. It stays exactly that — a sideloadable artifact — until this
request gets an answer.

## 4. One upstream code change worth making regardless of the above

Right now, a snap-packaged `herdr` would hit the in-TUI update toast's
"detach, run `herdr update`" guidance and then... run `herdr update`, which
the snap's wrapper has to refuse because `/snap` is read-only. That refusal
is handled for the CLI entry point already (see the packaging repo above),
but the *toast and guidance text itself* come from inside the binary, which
has no snap branch at all. This mirrors the existing Nix branch in
`src/update.rs` closely enough that it's a mechanical addition, not a design
question:

- `const SNAP_UPDATE_COMMAND: &str = "sudo snap refresh herdr";` beside
  `NIX_UPDATE_COMMAND` (`src/update.rs:31`)
- `fn is_snap_managed_exe_path(path: &Path) -> bool { path.starts_with("/snap/") }`
  beside `is_nix_store_exe_path` (`src/update.rs:2062`)
- `is_snap_managed_exe_path_following_links` and `is_snap_managed_install`,
  copying the two-line canonicalize pattern of the Nix helpers
  (`src/update.rs:2044`, `:1970`)
- branches in `update_install_command` (`src/update.rs:1931`),
  `update_install_instruction` (`:1943`),
  `package_manager_channel_update_guidance_for_current_install` (`:1994`),
  `preview_channel_rejection_for_exe_path` (`:2007`),
  `is_package_manager_managed_exe_path` (`:2024`), and the refusal chain in
  `self_update` (`:2183`)
- the free win worth naming: `is_package_manager_managed_exe_path` also gates
  `resolve_install_source` in `src/remote/attach.rs:2129`, so a snap install
  would correctly download the release asset when seeding a remote machine,
  instead of trying to copy a path under `/snap`
- tests mirroring the existing Nix cases at `src/update.rs:3156` and `:3247`

Happy to open this as a PR against `herdrdev/herdr` once I'm on the approved-
contributor list, or to hand the diff over directly — whichever is less
friction for the maintainers.

---

**Not yet posted.** This file is the text to send; actually opening the
GitHub Discussion and sending the `hey@herdr.dev` email are left for a human
to trigger (or explicitly authorize) rather than done automatically by this
packaging work. The companion step — a short, non-duplicative note on forum
topic 52894 and on @leko's `lekoOwO/herdr-snap` pointing at this effort — is
likewise left unsent for the same reason.
