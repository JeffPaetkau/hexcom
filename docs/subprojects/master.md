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

What each increment was run on — the model from the `Co-Authored-By` trailer the harness adds,
and whether the session was fresh or continued from the `Session:` trailer `CLAUDE.md` asks for:

```bash
git log --format='%h %s%n   %(trailers:key=Co-Authored-By,valueonly)%(trailers:key=Session,valueonly)' -20
```

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

### 5. Say what to run the next job on

Asked for by the user, because the tokens are the budget. For each territory with a brief ready,
two recommendations: **keep the running session or start a fresh one**, and **which model** —
Opus 5 or Fable 5.1. They interact, and the reasoning is in the entry 045; the short form:

- **A fresh session costs its reading.** With the reading rule in `CLAUDE.md` that is the map,
  one doc in full, four heads, the open entries and the section of the design doc the job
  touches — tens of thousands of tokens, once. A continued session costs its accumulated
  context on every turn, and the context only grows. So a session pays to continue *per turn*
  and pays to restart *once*: continue when the next job is on the same files and the session
  has done one or two jobs; restart when it has done three, or when the job changes shape.
- **Opus for a brief that says what to build; Fable for a job that has to decide what the brief
  should have said.** The briefs are written to be sufficient prompts, and most jobs are the
  first kind. The second kind is the greybox — it rewrites `game/` and is the moment `map.md`
  says to look at the View split again — and anything on the AI's search, where the last four
  entries from real ground are all about what a one-step search does wrong.
- **Never restart to change model if the job is one turn from done.** The cold start is the
  whole cost, and a session at its last turn has already paid its context.

Read the trailers off `git log` (section 1 above) before saying any of this; the trailers are
the only record of what a session was, and they are the reason the recommendation can be
derived rather than remembered.

### 6. Rebuild the executable after each round

Asked for by the user, entry 055: the game is tested by playing it, so every round of merges
ends with a fresh build the user can double-click. **The command is View's and lives under
`## Shipping it` in `subprojects/view.md`; Master pastes it and does not edit it.** The output
is `build/` at the repository root, which is ignored by git — a built game is derived, like a
test result, and nothing checked in is a claim about whether it builds.

The order within a round: merge, `dotnet test`, the map and the log, commit and push, **then**
the build, so that what is built is what was pushed. Report the path to the user and nothing
else about it.

**Check the game is not running first** — `tasklist | grep -i hexcom`. Windows will not let the
exporter replace a running `Hexcom.exe`; the export completes, exits 0, and leaves a full-size
`Hexcom.tmp` beside an unchanged `.exe`. That is the user playing the last build, which is the
point of the whole exercise, so ask rather than kill. Send the exporter's output to a file rather
than through a pipe with `head` on it, which can close early and end the run.

If the build fails, that is a finding for View in `decisions.md`, with the output — not a fix.
Master runs a build; it does not own one. The one exception is templates or a tool missing from
this machine, which is environment and not code, and which `view.md` should say how to put
back.

---

## Push back

Standing instruction from the user: **if one of their ideas looks wrong, say so, with the
reasoning, before doing it.** Skeptical is enough; it does not have to be certainly wrong. Master
sees the whole breakdown and the user sees the game, and the point of the role is the view
across territories — an idea that is fine for one and costly for three is exactly what Master
exists to notice. Say what it costs, what it would break, or what already answers it; then, if
the user holds to it, do it and record in the log that it was argued, so the next session does
not re-argue it. A recommendation is not a refusal, and the decision stays theirs.

---

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
