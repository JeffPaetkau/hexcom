using System.Collections.Generic;
using Hexcom.Core.Maps;

namespace Hexcom.Content;

/// <summary>
/// A map as read from a file: the <see cref="BattleMap"/> the rules run on, plus the things the
/// file declared around it that a view or an editor might want to list.
/// </summary>
/// <param name="Name">Whatever the file's <c>map</c> line said, or the file name, or nothing.</param>
/// <param name="Map">The authored battlefield, ready to hand to a <c>Battle</c>.</param>
/// <param name="Profiles">Every wall profile the file can name, built-in and declared alike.</param>
/// <param name="Grounds">Every ground type the file can name, built-in and declared alike.</param>
public sealed record MapDocument(
    string? Name,
    BattleMap Map,
    IReadOnlyDictionary<string, WallProfile> Profiles,
    IReadOnlyDictionary<string, GroundType> Grounds);
