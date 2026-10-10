"""Names of objects, materials, collections and images (CLAUDE.md rule 4, spec 18 §4.3).

Every data-block a part makes is `<Part>[.L|.R|.C].<Component>...`, e.g. `Boot.L.Sole.Lugs`; left and
right are the soldier's own. A part owns the names under its prefixes (`Boot.`), which is how a
re-run finds and replaces its own data and nothing else.
"""
import re

PATTERN = re.compile(r"^[A-Z][A-Za-z0-9]*(\.(L|R|C))?(\.[A-Za-z0-9_]+)*$")
# Blender answers a taken name with `.001`, `.002`, ...; such a name in a build always means an old
# data-block was not replaced, so it is refused although PATTERN would accept it.
DUPLICATE = re.compile(r"\.\d{3}$")
# A part's prefix: a capitalised first token, so it can never match MPFB's lower-case groups and keys.
PREFIX = re.compile(r"^[A-Z][A-Za-z0-9]*(\.[A-Za-z0-9_]+)*\.$")
PARTS = "Parts"  # the collection that holds every PartNN.<Name> collection
SIDES = ("L", "R", "C")


def valid(n):
    return bool(PATTERN.match(n)) and not DUPLICATE.search(n)


def check(n):
    if not valid(n):
        raise ValueError(f"bad name {n!r}: expected <Part>[.L|.R|.C].<Component>... "
                         "(capitalised first token, no Blender .001 suffix)")
    return n


def name(part, side=None, *components):
    """name("Boot", "L", "Sole", "Lugs") -> "Boot.L.Sole.Lugs"; side None for an unsided part."""
    if side is not None and side not in SIDES:
        raise ValueError(f"side must be one of {SIDES}, not {side!r}")
    return check(".".join([part] + ([side] if side else []) + [str(c) for c in components]))


def mirror_name(n):
    """The other side's name: each L token becomes R and back; centre and unsided names are kept."""
    swap = {"L": "R", "R": "L"}
    return ".".join(swap.get(t, t) for t in n.split("."))


def collection_name(part_id, part_name):
    """("02", "boots") -> "Part02.Boots"; ("13", "plate_carrier") -> "Part13.PlateCarrier"."""
    title = "".join(w[:1].upper() + w[1:] for w in part_name.split("_"))
    return check(f"Part{part_id}.{title}")


def check_prefix(p):
    if not PREFIX.match(p):
        raise ValueError(f"bad prefix {p!r}: expected a capitalised token ending in a dot, e.g. 'Boot.'")
    return p


def owned(n, prefixes):
    """True if the name falls under one of a part's prefixes (`Boot.` owns `Boot.L.Sole`, not `Bootlace`)."""
    return any(n.startswith(p) for p in prefixes)


def selftest():
    assert name("Boot", "L", "Sole", "Lugs") == "Boot.L.Sole.Lugs"
    assert name("Body", None, "Mesh") == "Body.Mesh"
    for good in ("Part02.Boots", "Body.Mesh", "Boot.L.Sole.Row01", "Rifle.Rail.Slot_7", "Morgan.Rig"):
        assert valid(good), good
    for bad in ("boot.L", "Boot L", "Boot.L.Sole.001", "Boot..Sole", "", "Boot.", "2Boot"):
        assert not valid(bad), bad
    for call in (lambda: name("Boot", "X", "Sole"), lambda: name("boot", "L"), lambda: check_prefix("boot.")):
        try:
            call()
            raise AssertionError("accepted a bad name")
        except ValueError:
            pass
    assert mirror_name("Boot.L.Sole") == "Boot.R.Sole" and mirror_name("Boot.R.Sole") == "Boot.L.Sole"
    assert mirror_name("Rifle.Body") == "Rifle.Body" and mirror_name("Belt.C.Buckle") == "Belt.C.Buckle"
    assert collection_name("13", "plate_carrier") == "Part13.PlateCarrier"
    assert owned("Boot.L.Sole", ("Boot.",)) and not owned("Bootlace.L", ("Boot.",))
    assert check_prefix("Body.Face.") == "Body.Face."
    return {"pattern": PATTERN.pattern}
