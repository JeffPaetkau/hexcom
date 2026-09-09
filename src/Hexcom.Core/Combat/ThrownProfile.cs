namespace Hexcom.Core.Combat;

/// <summary>
/// A charge, as data: what it does, how far it reaches and how much racket it makes. Content and
/// balance, not rules.
/// </summary>
/// <remarks>
/// Deliberately not a <see cref="WeaponProfile"/> with an odd fire mode on it, and that was the
/// first thing this had to settle. A shot has a shooter, a target and a face; everything from
/// <see cref="Gunnery.HitChance"/> to the reaction timeline is built on those three. A charge has
/// a landing point and a radius, hits whoever happens to be standing near it including your own
/// side, and cannot miss — there is no target for it to miss. Sharing a type with a rifle would
/// have meant a target field nothing sets and a hit chance nothing rolls.
/// <para>
/// What it does share is everything below the skin. The layers a blast meets on each face are
/// exactly the layers a round meets, so <see cref="Protection.Preview"/> answers for both, and a
/// blast is expressed as a <see cref="ShotExpectation"/> per soldier caught so that the scorer
/// can weigh a grenade against a shot without a second currency.
/// </para>
/// <para>
/// The same profile is thrown and laid. A mine is not a different explosive from a grenade; it is
/// the same charge left somewhere with a trigger on it rather than lobbed, which is why there is
/// one cost here rather than two.
/// </para>
/// </remarks>
/// <param name="Kind">
/// Which family the blast belongs to, and therefore which layer stops it. Fragmentation is
/// kinetic, so plate stops it and a force shield barely notices — which makes a grenade the
/// standing answer to a shielded soldier, exactly as a beam is the answer to an armoured one.
/// </param>
/// <param name="Damage">What it does to somebody standing at the centre of it, before layers.</param>
/// <param name="Radius">Metres from the burst at which it does nothing at all.</param>
/// <param name="MaxThrow">Metres it can be thrown, measured along the ground.</param>
/// <param name="MaxArc">
/// The highest, in metres above the straight line to the landing point, that it can be lofted.
/// This is what decides whether a wall can be thrown over: see <see cref="Vision.LobSolver"/>.
/// </param>
/// <param name="ApCost">
/// What throwing it, or laying it, costs off the price list. One number for both, because they
/// are the same handful of seconds spent on the same object.
/// </param>
/// <param name="Loudness">
/// Noise the burst makes, in the units movement uses. Loud: an explosion is the loudest thing on
/// the field, and it is heard from <em>where it went off</em> rather than from where it was
/// thrown, which is most of what makes one useful for reasons other than damage.
/// </param>
public sealed record ThrownProfile(
    string Id,
    string Name,
    DamageKind Kind,
    int Damage,
    double Radius,
    double MaxThrow,
    double MaxArc,
    int ApCost,
    double Loudness)
{
    /// <summary>Standard fragmentation grenade. The answer to a man behind a wall.</summary>
    public static readonly ThrownProfile FragGrenade = new(
        Id: "frag_grenade",
        Name: "Frag grenade",
        Kind: DamageKind.Kinetic,
        Damage: 14,
        Radius: 4.0,
        MaxThrow: 20.0,
        MaxArc: 6.0,
        ApCost: 20,
        Loudness: 70);

    /// <summary>
    /// A shaped plasma charge. Beam family, so it goes through plate and a shield eats it.
    /// </summary>
    /// <remarks>
    /// Shorter reach and a tighter burst than fragmentation, because it is a demolition charge
    /// being used for something else. It is what a beam squad carries for the same reason a
    /// beam squad carries beams, and it is the wrong thing to throw at a shielded target.
    /// </remarks>
    public static readonly ThrownProfile PlasmaCharge = new(
        Id: "plasma_charge",
        Name: "Plasma charge",
        Kind: DamageKind.Beam,
        Damage: 18,
        Radius: 3.0,
        MaxThrow: 14.0,
        MaxArc: 4.0,
        ApCost: 25,
        Loudness: 55);

    /// <summary>
    /// A directional mine. Heavy, barely throwable, and meant to be left somewhere.
    /// </summary>
    /// <remarks>
    /// The throw figures are deliberately poor rather than absent: you <em>can</em> lob one, badly
    /// and not far, and there is no reason for the rules to forbid it. What it is for is denying
    /// ground while you are somewhere else.
    /// </remarks>
    public static readonly ThrownProfile Claymore = new(
        Id: "claymore",
        Name: "Claymore",
        Kind: DamageKind.Kinetic,
        Damage: 20,
        Radius: 3.0,
        MaxThrow: 6.0,
        MaxArc: 2.0,
        ApCost: 20,
        Loudness: 75);
}

/// <summary>
/// The dials on things that go off. All balance, no structure.
/// </summary>
/// <remarks>
/// The eighth home was <c>UtilityModel</c> and this is the ninth, which wants justifying rather
/// than merely announcing. A blast is not shooting: nothing about it is a hit chance, a range
/// band or a cover penalty, and the two figures below have no counterpart anywhere in
/// <see cref="GunneryModel"/>. Folding them in there would have meant a record whose name
/// stopped describing half its contents. See <c>docs/decisions.md</c>.
/// <para>
/// It is a short list on purpose, and two things a reader will look for are deliberately not
/// here. <b>Falloff</b> is not a dial: a blast runs from full at the centre to nothing at the
/// radius, in a straight line, because that is the only shape a player can read off a ring drawn
/// on the map, and a curve nobody can see on screen is a number nobody can play around. <b>What
/// a stance is worth against a blast</b> is not a dial either — it is derived, from the
/// silhouette heights that art is already committed to. A prone soldier is a quarter of the
/// height of a standing one and catches a quarter of the wave, and if the stance heights ever
/// move, this moves with them rather than drifting away from them.
/// </para>
/// </remarks>
public sealed record BlastModel
{
    public static readonly BlastModel Default = new();

    /// <summary>
    /// How far above the floor the charge goes off, in metres.
    /// </summary>
    /// <remarks>
    /// Ankle height, and it matters more than it sounds. The burst point is where the sight trace
    /// to each soldier caught starts from, so a low burst is shadowed by low cover: a knee-high
    /// wall between you and a grenade on the ground really does take most of it, while the same
    /// wall does nothing about one that came down on your side. That is the whole tactical point
    /// of the arc, and it comes out of this number and the ordinary waterline geometry rather
    /// than out of a rule about cover and explosions.
    /// </remarks>
    public double BurstHeight { get; init; } = 0.3;

    /// <summary>
    /// How much of a charge a soldier with no line at all to the burst still catches.
    /// </summary>
    /// <remarks>
    /// Nothing, and that is a position rather than an oversight. A solid wall between you and a
    /// grenade means the grenade did not happen to you, which is what makes cover worth taking
    /// and what makes lobbing one <em>over</em> the wall worth the trouble. Anything above zero
    /// would quietly pay the thrower for missing.
    /// <para>
    /// It is a dial rather than a constant because it is the obvious thing to turn up if blasts
    /// ever read as too easily dodged, and because the argument above is an argument rather than
    /// a measurement.
    /// </para>
    /// </remarks>
    public double ShelteredShare { get; init; } = 0.0;
}
