using System.Collections.Generic;
using System.Linq;
using Hexcom.Core.Battles;
using Hexcom.Core.Geometry;
using Hexcom.Core.Hexes;
using Hexcom.Core.Movement;
using Hexcom.Core.Units;
using Hexcom.Core.Vision;

namespace Hexcom.Core.Awareness;

/// <summary>
/// Who knows what about whom, and how they came to know it.
/// </summary>
/// <remarks>
/// This is the system the game is about, so it is worth being explicit about the shape of it.
/// There is no aggro radius anywhere. Every enemy that knows about you learned it through a
/// channel the player can see and cut:
/// <list type="bullet">
/// <item>Looking, which happens on the observer's own turn and depends on how much of you is
/// actually visible — the exposure figure the sight trace already returns.</item>
/// <item>Hearing, which happens the moment you move and reports a place rather than a person.
/// A sound alone can never make anyone certain.</item>
/// <item>Being told, by radio, by shouting, or by watching a comrade react. Only a unit with a
/// radio can reach the whole side, which is what makes the radio operator worth killing first
/// and quietly.</item>
/// </list>
/// <para>
/// Observation runs on the observer's turn rather than continuously, so a sentry that has
/// already acted this round will not notice you until it comes round again. That is a window,
/// and reading the turn order to find it is meant to be part of the approach.
/// </para>
/// </remarks>
public sealed class AwarenessTracker
{
    private readonly Battle _battle;
    private readonly Dictionary<(UnitId Observer, UnitId Subject), Contact> _contacts = [];

    internal AwarenessTracker(Battle battle, AwarenessModel model)
    {
        _battle = battle;
        Model = model;
    }

    public AwarenessModel Model { get; }

    // ---- reading ---------------------------------------------------------------

    /// <summary>
    /// The full record, certainty figure and all. For rules, AI and tests — not for the player.
    /// </summary>
    public Contact Of(UnitId observer, UnitId subject)
    {
        var key = (observer, subject);
        if (_contacts.TryGetValue(key, out var existing)) return existing;

        var fresh = new Contact(Model, observer, subject);
        _contacts[key] = fresh;
        return fresh;
    }

    /// <summary>What the interface is allowed to show about an enemy's state of mind.</summary>
    public AwarenessReadout ReadoutFor(UnitId observer, UnitId subject)
    {
        if (!_contacts.TryGetValue((observer, subject), out var contact)) return AwarenessReadout.Nothing;

        var since = contact.LastContactRound == 0 ? 0 : _battle.Round - contact.LastContactRound;
        return new AwarenessReadout(contact.State, contact.LastKnownPosition, since, contact.EyesOn);
    }

    /// <summary>Every record this observer holds, whether or not it amounts to anything.</summary>
    public IEnumerable<Contact> ContactsFor(UnitId observer)
        => _contacts.Values.Where(c => c.Observer == observer);

    /// <summary>Everyone currently hunting or fighting this observer's subject.</summary>
    public IEnumerable<Contact> ContactsOn(UnitId subject)
        => _contacts.Values.Where(c => c.Subject == subject);

    /// <summary>
    /// The worst it currently is for one unit: the highest state any enemy holds about it. This
    /// is the number a player watches when deciding whether the approach is still working.
    /// </summary>
    public AwarenessState HighestAwarenessOf(UnitId subject)
    {
        var worst = AwarenessState.Unaware;
        foreach (var contact in ContactsOn(subject))
            if (contact.State > worst) worst = contact.State;
        return worst;
    }

    /// <summary>True while nobody on the other side has so much as a suspicion.</summary>
    public bool IsUndetected(UnitId subject) => HighestAwarenessOf(subject) == AwarenessState.Unaware;

    /// <summary>Drop everything about a unit that has left the fight.</summary>
    internal void Forget(UnitId unit)
    {
        foreach (var key in _contacts.Keys.Where(k => k.Observer == unit || k.Subject == unit).ToList())
            _contacts.Remove(key);
    }

    // ---- the channels ----------------------------------------------------------

    /// <summary>
    /// One unit takes a look around, gaining on what it can make out and losing track of what
    /// it cannot, then passes on anything it is now sure of.
    /// </summary>
    /// <remarks>
    /// The turn loop calls this once as each unit ends its turn. Call it yourself only when
    /// something other than a turn ending should prompt a look — a unit on overwatch, or an AI
    /// weighing what it would see from somewhere else. Calling it twice for one turn hands that
    /// observer two turns worth of certainty.
    /// </remarks>
    public void Observe(Unit observer, int round)
    {
        foreach (var subject in _battle.Enemies(observer).ToList())
        {
            var contact = Of(observer.Id, subject.Id);
            var sight = _battle.Look(observer, subject);
            contact.EyesOn = sight.CanSee;

            var gain = sight.CanSee ? LookGain(observer, UnitPose.Of(subject), sight) : 0;

            if (gain > 0)
            {
                contact.Detection = Math.Min(contact.Detection + gain, Model.Ceiling);
                contact.LastKnownPosition = subject.Position;
                contact.LastContactRound = round;
            }
            else
            {
                contact.Detection = Math.Max(0, contact.Detection - Model.DecayPerTurn);
            }
        }

        foreach (var contact in ContactsFor(observer.Id).Where(c => c.Detection >= Model.AlertedAt).ToList())
            Relay(observer, contact, round);
    }

    /// <summary>
    /// A noise at a unit position. Everyone in earshot learns roughly where it came from.
    /// </summary>
    /// <remarks>
    /// Movement raises this on its own. It is public because doors, grenades and gunfire will
    /// all want to raise it too.
    /// </remarks>
    public void Hear(Unit source, double loudness, int round)
    {
        if (loudness <= 0) return;

        var radius = loudness * Model.NoiseMetresPerPoint;
        if (radius <= 0) return;

        var origin = _battle.Sight.Ground(source.Position);

        foreach (var listener in _battle.Enemies(source).ToList())
        {
            var distance = Vec3.GroundDistance(origin, _battle.Sight.Ground(listener.Position));
            if (distance > radius) continue;

            var contact = Of(listener.Id, source.Id);

            // A sound says where, not who. It can send someone to look, never make them certain.
            var gain = Model.NoiseGain * (1 - distance / radius);
            var raised = Math.Min(contact.Detection + gain, Model.AlertedAt - 1);
            if (raised <= contact.Detection) continue;

            contact.Detection = raised;
            contact.LastKnownPosition = source.Position;
            contact.LastContactRound = round;
        }
    }

    /// <summary>
    /// A unit does something visible: a muzzle flash, or the bright line a beam draws back to
    /// whoever fired it.
    /// </summary>
    /// <remarks>
    /// The counterpart to <see cref="Hear"/>, and the reason the two weapon families are not
    /// interchangeable. A slugthrower is silent until it fires and then everyone within a
    /// hundred metres knows roughly where you are. A beam makes no sound and is unmissable to
    /// anyone facing your way — and worth nothing at all to anyone who is not.
    /// </remarks>
    public void Reveal(Unit source, double brightness, int round)
    {
        if (brightness <= 0) return;

        foreach (var watcher in _battle.Enemies(source).ToList())
        {
            var sight = _battle.Look(watcher, source);
            if (!sight.CanSee) continue;

            var contact = Of(watcher.Id, source.Id);
            var gain = Model.LookGain * brightness * AttentionOn(watcher, source.Position);
            if (gain <= 0) continue;

            contact.Detection = Math.Min(contact.Detection + gain, Model.Ceiling);
            contact.LastKnownPosition = source.Position;
            contact.LastContactRound = round;
            contact.EyesOn = true;
        }
    }

    /// <summary>
    /// Being shot at settles the question of whether there is somebody out there. The target
    /// knows, whatever it could or could not see a moment ago.
    /// </summary>
    public void TakeFireFrom(Unit target, Unit shooter, int round)
    {
        var contact = Of(target.Id, shooter.Id);
        contact.Detection = Math.Max(contact.Detection, Model.AlertedAt);
        contact.LastKnownPosition = shooter.Position;
        contact.LastContactRound = round;

        Relay(target, contact, round);
    }

    /// <summary>
    /// Call a contact in deliberately: tell whoever can hear or see you what you have found.
    /// </summary>
    /// <remarks>
    /// The same channels as any other relay — radio to the whole side, otherwise a shout or a
    /// comrade watching you react. What makes this one worth an action is that it happens when
    /// <em>you</em> choose rather than when a threshold is crossed, which is what a soldier who
    /// has just been surprised and has nothing useful to shoot at does with the moment.
    /// </remarks>
    public void CallOut(Unit caller, UnitId subject, int round) => Relay(caller, Of(caller.Id, subject), round);

    /// <summary>Everyone who would actually hear a shout, so nobody is offered a pointless one.</summary>
    public IEnumerable<Unit> Earshot(Unit caller) => _battle.Allies(caller).Where(ally => CanReach(caller, ally));

    /// <summary>Pass a contact to whoever can be reached, at a discount.</summary>
    private void Relay(Unit caller, Contact source, int round)
    {
        foreach (var ally in _battle.Allies(caller))
        {
            if (!CanReach(caller, ally)) continue;

            var theirs = Of(ally.Id, source.Subject);
            var passed = source.Detection * Model.RelayFraction;
            if (passed <= theirs.Detection) continue;

            theirs.Detection = passed;
            theirs.LastKnownPosition = source.LastKnownPosition;
            theirs.LastContactRound = round;
        }
    }

    /// <summary>
    /// Radio reaches the whole side; a shout reaches nearby; and seeing a comrade react tells
    /// you something even if you heard nothing. Cutting the net means killing the radios.
    /// </summary>
    private bool CanReach(Unit caller, Unit ally)
    {
        if (caller.Stats.Radio) return true;
        if (_battle.CanSee(ally, caller)) return true;

        var apart = Vec3.GroundDistance(
            _battle.Sight.Ground(caller.Position),
            _battle.Sight.Ground(ally.Position));

        return apart <= Model.VoiceRangeMetres;
    }

    /// <summary>
    /// What one look is worth. Range tells against you gently at first and then sharply, so
    /// distance only starts hiding you once there is real ground between you.
    /// </summary>
    private double LookGain(Unit observer, UnitPose subject, SightResult sight)
    {
        if (sight.Distance >= Model.SightRangeMetres) return 0;

        var closeness = sight.Distance / Model.SightRangeMetres;
        var range = 1.0 - closeness * closeness;
        var acuity = observer.Stats.Perception / 10.0;
        var hiding = StanceProfile.For(subject.Stance).ConcealmentBonus;
        var attention = AttentionOn(observer, subject.Position);

        return Model.LookGain * acuity * range * attention * sight.Exposure / hiding;
    }

    /// <summary>
    /// One observer takes a look at one subject standing somewhere in particular, rather than at
    /// everybody at once.
    /// </summary>
    /// <remarks>
    /// For looks that are not the once-per-turn sweep <see cref="Observe"/> does: a watchman
    /// registering movement across the arc it declared, at the tick the movement happens. The
    /// pose is passed in because inside a reaction window the interesting question is what the
    /// watchman makes of the mover <em>at that moment on the timeline</em>, which may be several
    /// hexes from where the move started.
    /// <para>
    /// Everything else about it is an ordinary look. Stance, cover, range, exposure, perception
    /// and which way the observer is facing all apply, so a careful approach is as invisible to a
    /// watchman as it is to anybody else.
    /// </para>
    /// </remarks>
    public double Notice(Unit observer, Unit subject, UnitPose where, int round)
    {
        var sight = _battle.Sight.Trace(observer.Vantage, where.Vantage);
        if (!sight.CanSee) return 0;

        var gain = LookGain(observer, where, sight);
        if (gain <= 0) return 0;

        var contact = Of(observer.Id, subject.Id);
        contact.Detection = Math.Min(contact.Detection + gain, Model.Ceiling);
        contact.LastKnownPosition = where.Position;
        contact.LastContactRound = round;
        contact.EyesOn = true;

        return gain;
    }

    /// <summary>
    /// How much of an observer's attention a place has, from one directly ahead down to a
    /// fraction behind.
    /// </summary>
    /// <remarks>
    /// Facing changes how readily something is noticed, never whether it could be seen at all.
    /// Line of sight stays pure geometry in the sight solver; who is paying attention to what is
    /// a question about people, and it belongs here. Coming at a sentry from behind is worth
    /// roughly twelve times the walk it costs.
    /// </remarks>
    public double AttentionOn(Unit observer, NodeId place)
    {
        // The edges of these arcs are not hypothetical: a hex directly north of a sentry looking
        // north-east lies at exactly sixty degrees, the edge of the front cone. One spoke over is
        // the corner of the eye, and the slack is what makes that a decision rather than whatever
        // 60.00000000000001 happens to compare as today.
        var away = _battle.AngleOffDegrees(observer.Position, observer.Facing, place)
                   + Geometry2D.AngleEpsilonDegrees;

        if (away <= Model.FrontArcDegrees / 2) return 1.0;
        if (away <= Model.PeripheralArcDegrees / 2) return Model.PeripheralAcuity;
        return Model.RearAcuity;
    }

    /// <summary>Whether a place falls inside the arc an observer is properly watching.</summary>
    public bool IsWatching(Unit observer, NodeId place) => AttentionOn(observer, place) >= 1.0;
}
