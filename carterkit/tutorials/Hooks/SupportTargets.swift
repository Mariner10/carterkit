import Foundation

// MARK: - Targets (tutorials spec 2.4)
//
// Namespaced ids published by the `supportTarget("…")` view modifier. Fixed ids are
// listed verbatim; dynamic ones are patterns with `<param>` segments. Enumerated
// params (`<section>`, `<mode>`) are closed by mirroring the app's own enums, so a new
// Layout Info section or header pane becomes targetable the moment it exists.

enum SupportTargets {
    static let fixed: [String] = [
        // the landing feed (first run, empty library, Help -> Welcome)
        "landing.startBlank", "landing.tour",
        // header + canvas
        "header.title", "header.connection", "header.pipes", "header.studio", "header.settings", "header.tabs",
        "canvas",
        // picker / templates / studio / editor
        "picker.heading", "picker.search", "picker.pinned", "picker.layouts", "picker.actions", "picker.templates",
        "templates.featured", "templates.starters", "templates.load",
        "studio.create", "studio.new", "studio.claude", "studio.connect", "studio.input",
        "editor.canvas", "editor.add", "editor.tray", "editor.inspector", "editor.attributes", "editor.save", "editor.agent",
        // the tutorials' pose hooks (aif-6jc0k.4)
        "editor.binding", "editor.try", "editor.pose.more", "editor.pose.done", "editor.pose.bars",
        // connection / settings
        "connection.status", "connection.hub", "connection.qr",
        "settings.feed", "settings.paywall",
        // §19.1 pane
        "pane", "pane.grabber", "pane.search", "pane.recent", "pane.row.current",
        "pane.actions", "pane.actions.studio", "pane.actions.templates", "pane.actions.scan",
        "hub.connection", "hub.info", "hub.hubs", "hub.pipes", "hub.studioSession", "hub.details",
        // §19.1 info
        "info", "info.tabs", "info.apply",
    ]

    /// Dynamic ids. `<id>`-style params match one dot-free segment unless they end the
    /// pattern (then the rest of the id); closed params match only their listed values.
    static let patterns: [String] = [
        "canvas.tab.<n>",
        "control.<id>",
        "group.<id>",
        "templates.card.<id>",
        "editor.tray.<type>", "editor.addChoice.<id>", "editor.addIntent.<intent>", "editor.attributes.<field>",
        "editor.chip.<chip>", "editor.petal.<field>", "editor.pose.more.<item>",
        "settings.row.<id>",
        "xray.control.<id>",
        "pane.row.<layoutId>.pin", "pane.row.<layoutId>.reorder", "pane.row.<layoutId>",
        "menu.row.<id>",
        "info.section.<section>",
        "info.card.<section>.<slug>",
    ]

    /// Closed values for enumerated params.
    static var closedParams: [String: [String]] {
        ["section": SupportRegistry.infoSections, "mode": SupportRegistry.paneModes]
    }

    /// Does this build know the target id (fixed or matching a pattern)?
    static func isKnown(_ id: String) -> Bool {
        if fixed.contains(id) { return true }
        return patterns.contains { matches(id, pattern: $0) }
    }

    /// Match one id against one pattern.
    static func matches(_ id: String, pattern: String) -> Bool {
        let idParts = id.split(separator: ".", omittingEmptySubsequences: false).map(String.init)
        let patParts = pattern.split(separator: ".").map(String.init)
        return match(idParts[...], patParts[...])
    }

    private static func match(_ id: ArraySlice<String>, _ pat: ArraySlice<String>) -> Bool {
        guard let p = pat.first else { return id.isEmpty }
        guard let s = id.first, !s.isEmpty else { return false }
        if p.hasPrefix("<"), p.hasSuffix(">") {
            let name = String(p.dropFirst().dropLast())
            if let closed = closedParams[name] {
                return closed.contains(s) && match(id.dropFirst(), pat.dropFirst())
            }
            if pat.count == 1 { return true }   // trailing open param: takes the rest (ids may contain dots)
            return match(id.dropFirst(), pat.dropFirst())
        }
        return p == s && match(id.dropFirst(), pat.dropFirst())
    }

    // MARK: Places (tutorial context spec 1.1, 2 rule 13)

    /// The places a target can be on screen in (`SupportPlace` raw values), so the lint can tell a step that runs in the
    /// editor not to point at "New Layout". Matched by id prefix, most specific first; an unlisted id is `[]`.
    static func places(of id: String) -> [String] {
        isKnown(id) ? rulePlaces(id) : []
    }

    /// Prefix rules alone, no known-id check: a pattern with a closed param (`<section>`) can't match its own placeholder.
    private static func rulePlaces(_ id: String) -> [String] {
        let editorish = ["editor", "pose", "try"]
        let rules: [(String, [String])] = [
            ("editor.addChoice.", ["pose"]), ("editor.addIntent.", ["pose"]),
            ("editor.chip.", ["pose", "try"]), ("editor.petal.", ["pose"]),
            ("editor.attributes", editorish), ("editor.binding", ["pose"]),
            ("editor.try", editorish), ("editor.add", ["editor"]),
            ("editor.", editorish),
            ("control.", ["canvas", "editor", "pose", "try"]), ("group.", ["canvas", "editor", "pose", "try"]),
            ("xray.", ["canvas"]), ("canvas", ["canvas"]),
            ("landing.", ["landing"]),
            ("studio.", ["studio"]),
            ("header.", ["canvas"]),
            ("picker.", ["canvas"]), ("pane", ["canvas"]), ("hub.", ["canvas"]), ("menu.", ["canvas"]),
            ("templates.", ["other"]), ("info", ["other"]), ("settings.", ["other"]), ("connection.", ["other"]),
        ]
        let hit = rules.first { rule in
            rule.0.hasSuffix(".") ? id.hasPrefix(rule.0) : (id == rule.0 || id.hasPrefix(rule.0 + "."))
        }
        return hit?.1 ?? []
    }

    /// Every fixed id and pattern with its places, for the registry export (`targetPlaces`).
    static var placeMap: [String: [String]] {
        Dictionary(uniqueKeysWithValues: (fixed + patterns).map { ($0, rulePlaces($0.replacingOccurrences(of: "<", with: "").replacingOccurrences(of: ">", with: ""))) })
    }
}
