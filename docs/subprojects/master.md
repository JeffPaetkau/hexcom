# Master — the map, the log, and the shape of the work

The session that owns how the work is divided, rather than any of the work. It writes no rules,
draws nothing, and authors no content. Point a session at this file when you want the state of
the project, a new brief written, or the breakdown itself argued about.

Read [../map.md](../map.md) first — this territory exists to keep that file true.

## Owns

```
CLAUDE.md                      the router, the conventions, the worktree policy
docs/map.md                    territories, path ownership, frozen contracts
docs/decisions.md              curation only — see the rules below
docs/subprojects/*.md          the doc *set* — creating, retiring, restructuring
```

**A territory owns the contents of its own doc.** Master creates it, may write or replace its
`## The job` brief, and owns the header sections that make the scheme work — Owns, Must not
touch, Depends on. Everything a territory learns and writes down for its successors is that
territory's. In practice the sessions doing the work keep their own docs current without being
asked, which is the scheme working rather than a boundary being crossed; Master's job here is
routing findings into briefs, not editing other people's notes.

`README.md` is shared. Each territory updates the parts its own work changed; Master owns only
its shape, and the territory paragraph near the top.

## Must not touch

All of `src/`, `tests/`, `game/`, `content/`, and `docs/design.html`. **Including to fix
something obviously broken.** A master session that reaches into Core to correct a bug it found
while auditing has just become a core session with no branch and no brief, and the finding it
should have written down is now a diff somebody else has to reverse-engineer. Write the entry.

## Does not use a worktree

Master works on `master` in the main directory. `CLAUDE.md` says a session that writes code takes
a worktree; this one does not write code, and a worktree for a doc edit is friction with nothing
to show for it. It also means Master is the session that can merge branches, since a branch can
only be checked out in one worktree at a time.

---

## The job — standing, not a one-off

Four things, roughly in the order they come up.

### 1. Derive status when asked

Never read it out of a file. Everything below is the truth; anything written down is a claim
about the past.

```bash
git branch -a              # what is in flight — a branch is a claim
git worktree list          # which sessions are live, and where
git log --oneline -25      # what has landed
dotnet test                # whether it works
```

Per territory: `git log --oneline -20 -- <its owned paths>`, from the table in `map.md`.

A territory is **in progress** if it has a branch or a worktree; **ready** if its doc's
`## The job` section describes work nothing blocks; **blocked** if the `Gated by` column names
something that has not happened yet. There is no fourth state that means anything.

### 2. Keep the map true

The things that rot, in the order they rot:

- **`Gated by` entries that have been lifted.** A gate is lifted by an entry in `decisions.md`,
  and nobody goes back to the table to say so. Check the resolved entries against the column.
- **Briefs that outlived their job.** A `## The job` section describes work that may have been
  finished two increments ago. Cross-check each against `git log` for that territory. The session
  that finishes a job is supposed to replace its brief with the next one; assume it did not.
- **Territories with no doc that now need one.** A doc is created when there is a brief to put in
  it. When a gate lifts, the territory behind it usually needs one the same day.
- **Worktrees nobody is coming back to.** Rule 6 says a territory minds its own and removes it
  once merged, which means the ones left over are the ones whose session ended before the merge —
  and by construction nobody but Master is allowed to look at them. `git worktree list` against
  `git branch --merged master`: anything merged and still on disk is yours to remove, and
  anything unmerged is somebody's unfinished work, so ask before touching it.
- **Checkable claims in `CLAUDE.md`.** Every section of it that describes the present is a status
  line wearing a disguise, and it is the one file no territory session may correct — so it rots
  unopposed, in front of the widest readership. It told every new session for weeks that Godot
  was not installed, which cost real work: sessions concluded no picture was available to them
  and hedged down to *it typechecks*. Re-read it whole, against the repository, on a schedule.
  See entries 015 and 016.
- **Contracts that have quietly stopped being true.** Contract 5 was violated by the sandbox for
  the whole of the project's life before anybody checked. Re-read the six in `map.md` against the
  code occasionally; that is the only thing that makes them contracts rather than wishes.
- **Sentences a closed entry invalidated and nobody went back for.** Every stale claim found so
  far was true when written and overtaken by a later entry — 014 settled the doc split and two
  passages in `view.md` still argued for it; 003 made an eighth home and `core.md` still said
  seven. So whenever an entry is flipped to `resolved`, grep the docs for what it superseded
  before moving on. See entry 019 for the count.

### 3. Curate `decisions.md`

**One field may be edited in place: `Status`.** Everything else in an entry is immutable —
never edit the text, never reorder, never renumber, never delete. An entry that turns out to be
wrong is superseded by a new one that says so, and the wrong one stays exactly as written.

The Status exception exists because an append-only log with no closable entries becomes a list
you cannot act on: it grows, everything reads as open, and the master's main instrument stops
working. Flipping one to `resolved` must name the entry that resolved it. If two branches flip
the same line the merge conflicts trivially; keep either.

What Master actually does here: reads new entries, works out which territory owes an answer,
and makes sure that answer is in that territory's brief rather than only in the log. **The log
is where findings arrive, not where they live.** An entry nobody has routed into a brief will be
read by nobody.

### 4. Write briefs

A brief goes in the territory's doc under `## The job`, and it is written so that
*read this file and do what it says* is a sufficient prompt. What one contains:

- the branch name, `<territory>/<slug>`
- where the seam already is, in code, by name — most work is smaller than it looks once the
  existing hook is named
- the decisions to settle **before** writing much, which are the ones that get made implicitly
  and are then expensive
- what is out of scope, and where a finding about it goes instead
- how to know it worked — a specific observable, not "tests pass"

A brief is a work order, not a status line: what to do, never how far along somebody got. That
distinction is the whole reason the doc set does not rot.

---

## Pending — stop Seafile syncing this repository

*A one-off, not part of the standing job. **Delete this section once it is done**, or it becomes
exactly the kind of stale claim the list above exists to hunt.*

This repository lives inside a synced Seafile library, and it should not. Git and GitHub are the
source of truth for every file here; Seafile is a second, dumber copy of the same history that
nobody reads and that nothing depends on.

**It is not merely redundant — it actively interferes.** Removing a merged worktree failed on
`.claude/worktrees/view+interface-audit`: git emptied the directory, then could not delete it,
and the empty folder was still locked minutes later.

```
error: failed to delete '...view+interface-audit': Permission denied
```

That is a sync client holding handles on files as they appear and vanish. Worktrees are now
standard for every session that writes code, so directories full of build output will be created
and destroyed constantly, and each one is a chance for the same failure — or worse, for a handle
held on something inside `.git` during a write.

**What was verified**, so the next session need not re-derive it:

| | |
|---|---|
| library root | `E:\Seafile\Personal` — `Personal` is one of six libraries under `E:\Seafile` |
| this repo | `E:\Seafile\Personal\Games\hexcom`, so `Games/hexcom/` relative to the root |
| existing ignore file | none, at the library root or any directory above the repo |
| client | `seafile-applet` was running |

**Two ways to fix it, and the second is cleaner.**

1. **Ignore it in place.** Seafile reads a `seafile-ignore.txt` at the library root, with
   gitignore-like patterns. Adding `Games/hexcom/` there is the small change. **Verify the
   behaviour before trusting it** — the pattern syntax is more restricted than gitignore's, and
   an ignore rule may only stop future uploads rather than withdraw what is already synced. The
   Seafile documentation is the authority, not this paragraph.
2. **Move the repository out of the library**, to something like `E:\code\hexcom`. No ignore
   semantics to get right and no sync client involved at all.

**If you move it, the path changes and some things are pinned to the old one** — the per-project
memory directory is named after the absolute path, `.claude/` may hold machine-local settings
with absolute paths in them, and any worktree registered under the old location must be pruned
first. Check `git worktree list` is empty, and expect to re-point rather than assume nothing
noticed.

Ask before doing either. Moving a repository out from under a sync client is the user's call,
not a tidy-up.

## What Master must not do

- **Do not write status into any file.** The temptation arrives disguised as helpfulness — one
  small "currently in progress" so the next session need not run `git branch`. It survives the
  session that wrote it and then misinforms everyone. This is the rule most likely to erode, and
  it is the load-bearing one.
- **Do not fix other territories' code.** See Must not touch above.
- **Do not republish the design doc.** That is Core's, and one artifact URL with two publishers
  is a conflict waiting to happen.
- **Do not create a doc with no brief in it.** An empty doc rots and looks maintained while
  doing it.

## Recent work

```bash
git log --oneline -20 -- CLAUDE.md docs/map.md docs/decisions.md docs/subprojects
```
