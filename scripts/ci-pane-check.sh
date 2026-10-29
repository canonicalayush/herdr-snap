#!/bin/sh
# Drives the installed herdr snap over its socket API to prove the launcher's
# environment scrub (snap/local/herdr-launch) reaches pane children, and that
# the invoking user's PATH (e.g. ~/.local/bin) is still usable from a pane.
#
# herdr is a TUI and refuses to attach without a properly sized pty ("terminal
# reported a zero-sized grid"), so it is launched inside a sized tmux pane
# rather than under `script`. `herdr pane list` and `pane read` return JSON,
# not a table, so this parses with jq. `herdr pane run <pane> <words...>`
# re-types the joined words through the pane's own interactive shell rather
# than passing them as an exec argv, so any command containing quoting or
# command substitution is run as a flat text file instead of inline.
set -eu

export PATH="$HOME/.local/bin:$PATH"

probe=/tmp/herdr-pane-probe.sh
cat > "$probe" <<'PROBE'
#!/bin/sh
echo "SNAPVARS=$(env | grep -c '^SNAP')"
fake-agent
PROBE
chmod +x "$probe"

tmux kill-session -t ci 2>/dev/null || true
tmux new-session -d -s ci -x 200 -y 50 "herdr --session ci 2>&1 | tee /tmp/herdr-tui.log"

# First run shows a welcome modal (dismiss with Enter), then an optional
# agent-integrations modal (dismiss with Escape). Socket calls below do not
# depend on either being dismissed, but dismissing keeps the transcript clean
# for diagnostics if something else fails.
sleep 2
tmux send-keys -t ci Enter
sleep 1
tmux send-keys -t ci Escape
pane=""
for _ in $(seq 1 30); do
    pane=$(herdr --session ci pane list 2>/dev/null | jq -r '.result.panes[0].pane_id // empty')
    [ -n "$pane" ] && break
    sleep 1
done
if [ -z "$pane" ]; then
    echo "no pane after 30s" >&2
    cat /tmp/herdr-tui.log >&2 2>&1 || true
    tmux capture-pane -t ci -p >&2 2>&1 || true
    exit 1
fi

# Give the pane's interactive shell time to finish starting up (readline
# enables bracketed paste on an interactive prompt); issuing `pane run`
# too early can race that and leak raw paste escape bytes into the shell.
sleep 3

ran=0
for _ in $(seq 1 5); do
    herdr --session ci pane run "$pane" "$probe"
    sleep 2
    probe_out=$(herdr --session ci pane read --source recent --lines 50 "$pane" 2>/dev/null || true)
    case "$probe_out" in
        *fake-agent-ok*) ran=1; break ;;
        *) sleep 2 ;;
    esac
done
[ "$ran" = 1 ] || { echo "pane run never executed cleanly" >&2; echo "$probe_out" >&2; exit 1; }

out=""
for _ in $(seq 1 20); do
    out=$(herdr --session ci pane read --source recent --lines 200 "$pane" 2>/dev/null || true)
    case "$out" in *fake-agent-ok*) break ;; esac
    sleep 1
done

status=0
case "$out" in
    *SNAPVARS=0*) ;;
    *) echo "snap vars leaked into pane" >&2; echo "$out" >&2; status=1 ;;
esac
case "$out" in
    *fake-agent-ok*) ;;
    *) echo "~/.local/bin not on pane PATH" >&2; echo "$out" >&2; status=1 ;;
esac

herdr --session ci server stop >/dev/null 2>&1 || true
tmux kill-session -t ci 2>/dev/null || true
exit "$status"
