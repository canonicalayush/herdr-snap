# herdr-snap

Unofficial classic-confinement snap packaging for [herdr](https://github.com/herdrdev/herdr),
a terminal multiplexer built for coding agents. This repository repacks upstream's
published release binaries; it does not build herdr from source and does not modify
herdr's behaviour beyond a thin launcher that scrubs snapd's environment before exec
and intercepts self-update (see `snap/local/herdr-launch`).

This snap is **not currently published to the Snap Store**. The Snap Store rejected a
prior community classic-confinement request for this name on publisher-vetting grounds
(see `docs/upstream-adoption.md` and `docs/classic-confinement-request.md` for the full
history and the conditions under which a request would be filed). Until then, install by
sideloading a built `.snap`:

```
sudo snap install --classic --dangerous ./herdr_<version>_<arch>.snap
```

Once store publication is possible, snapd's four-times-a-day auto-refresh against the
`stable` channel is what replaces `herdr update` for snap users; `herdr update` and
`herdr channel set` are intercepted by the launcher and refused in favour of
`sudo snap refresh herdr`.
