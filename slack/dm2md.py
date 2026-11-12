#!/usr/bin/env python3
"""Convert a Slackdump `dump` JSON file into a Markdown transcript.

Usage:
    python3 dm2md.py <input>.json [-o OUTPUT] [--tz ZONE]
        [--name U0AAAAAAA=Alice] [--name U0BBBBBBB=Bob]

The conversation ID comes from the JSON's "channel_id". The output defaults
to <input>.md next to the JSON. Attachment links point at
<ID>/<FileID>-<filename>, where Slackdump saves files. Users without a
--name appear by user ID. Needs Python 3.9+ and the standard library only.
"""
import argparse
import datetime as dt
import json
import os
import re
import sys

#===============================================================================
# Helpers


def get_tz(name):
    """Return a tzinfo for an IANA zone name, or None for system local."""
    try:  # Windows Python may lack the tzdata package.
        from zoneinfo import ZoneInfo
        return ZoneInfo(name)
    except (ImportError, KeyError, ValueError):
        print(f"warning: time zone {name!r} unavailable; using system local "
              "time", file=sys.stderr)
        return None


def local(ts, tz):
    t = dt.datetime.fromtimestamp(float(ts), dt.timezone.utc)
    return t.astimezone(tz) if tz else t.astimezone()


def stamp(ts, tz):
    return local(ts, tz).strftime("%Y-%m-%d %a %I:%M %p %Z")


def who(m, names):
    uid = m.get("user") or m.get("username") or m.get("bot_id") or "unknown"
    return names.get(uid, uid)


def clean(s, names):
    s = re.sub(r"<@([UW]\w+)(?:\|[^>]*)?>",
               lambda m: "@" + names.get(m.group(1), m.group(1)), s or "")
    s = re.sub(r"<#\w+\|([^>]+)>", r"#\1", s)
    s = re.sub(r"<!(here|channel|everyone)(?:\|[^>]*)?>", r"@\1", s)
    s = re.sub(r"<(https?://[^|>]+)\|([^>]+)>", r"[\2](\1)", s)
    s = re.sub(r"<(https?://[^>]+)>", r"\1", s)
    return s.replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&")


def files(m, cid):
    out = []
    for f in m.get("files") or []:
        name = f.get("name") or f["id"]
        out.append(f"[{name}](<{cid}/{f['id']}-{name}>)")
    return out


def block(m, names, cid, tz):
    lines = [f"**{who(m, names)}**, {stamp(m['ts'], tz)}", ""]
    lines += clean(m.get("text"), names).splitlines() or [""]
    fl = files(m, cid)
    if fl:
        lines += ["", "Files: " + ", ".join(fl)]
    return lines + [""]


def replies(m):
    # Slackdump repeats the thread parent in its reply list; skip it.
    reps = [r for r in (m.get("slackdump_thread_replies") or [])
            if r.get("ts") != m.get("ts")]
    return sorted(reps, key=lambda r: float(r["ts"]))

#===============================================================================
# Main


def parse_name(s):
    uid, sep, name = s.partition("=")
    if not (sep and uid.strip() and name.strip()):
        raise argparse.ArgumentTypeError(f"expected UID=NAME, got {s!r}")
    return uid.strip(), name.strip()


def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("input", help="Slackdump JSON, e.g., D0123456789.json")
    p.add_argument("-o", "--output", help="output path (default: <input>.md)")
    p.add_argument("--tz", default="America/New_York",
                   help="IANA time zone (default: %(default)s)")
    p.add_argument("--name", action="append", type=parse_name, default=[],
                   metavar="UID=NAME",
                   help="display name for a user ID; repeatable")
    args = p.parse_args()
    out_path = args.output or os.path.splitext(args.input)[0] + ".md"
    names = dict(args.name)
    tz = get_tz(args.tz)

    with open(args.input, encoding="utf-8") as fh:
        d = json.load(fh)
    cid = (d.get("channel_id")
           or os.path.splitext(os.path.basename(args.input))[0])
    msgs = sorted(d["messages"], key=lambda m: float(m["ts"]))
    n_rep = sum(len(replies(m)) for m in msgs)
    people = []
    for m in msgs:
        for x in [m] + replies(m):
            if who(x, names) not in people:
                people.append(who(x, names))
    dumped = local(os.path.getmtime(args.input), tz).strftime(
        "%Y-%m-%d %H:%M %Z")
    out = [
        f"# Slack conversation `{cid}`", "",
        f"Dumped with Slackdump on {dumped}; transcript generated from "
        f"`{os.path.basename(args.input)}`.",
        f"Participants: {', '.join(people)}.",
        f"Messages: {len(msgs)} top-level, {n_rep} thread replies. Times in "
        f"{args.tz if tz else 'system local time'}. Attachments live in "
        f"`{cid}/`.", "",
    ]
    day = None
    for m in msgs:
        mday = local(m["ts"], tz).strftime("%Y-%m-%d %A")
        if mday != day:
            out += [f"## {mday}", ""]
            day = mday
        out += block(m, names, cid, tz)
        reps = replies(m)
        if reps:
            out += [f"> Thread ({len(reps)} replies)", ">"]
            for r in reps:
                out += [("> " + x) if x else ">"
                        for x in block(r, names, cid, tz)]
            out.append("")
    with open(out_path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(out))
    print(f"{len(msgs)} top-level, {n_rep} replies -> {out_path}")


if __name__ == "__main__":
    main()
