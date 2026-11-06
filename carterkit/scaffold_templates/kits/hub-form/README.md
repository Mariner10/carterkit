# __NAME__: a form that submits to the hub

**What it shows.** A form (a group with a `form` block in `layout.json`): a name, a count
stepper, a picker and an Urgent toggle. What you type stays a draft on the phone, checked
against the form's rules there (Send stays disabled until the draft is valid). Send submits
the whole draft once, as one `form_submit` command with `{{form}}` in its payload, and the
form clears. The hub checks the entry again with its own rules (a duplicate name is
refused), keeps it, and answers with a status line and the list of what it received.

**Run it.**

```bash
python hub.py              # prints a QR: in CAR-TER open the layout list, tap Scan
carterkit validate layout.json
```

The pairing is kept in `.carterkit/session.json`, so the next run reconnects without a
scan. Every save of `hub.py` or `layout.json` is pushed to the phone. Have a Connect+ hub
credential? Save it as `secrets/hub.json` to use the managed relay instead of your LAN.

**Change first.**

1. The fields: the inputs inside the `entry-form` group and their rules in `form.fields`
   (`required`, `min`, `max`, `minLength`, `maxLength`, `oneOf`, `kind`).
2. `check()` in `hub.py`: the rules the hub enforces whatever the phone sends.
3. What happens to an entry: `entries.append(...)` in `submitted`; write it to a file, a
   database or another service.
