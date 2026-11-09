import Foundation

// MARK: - Registry export (tutorials spec 2.4)
//
// `SupportRegistry.export()` produces the hooks registry, written by `SupportRegistryExportTests` on every test run
// and committed as `CAR-TER/Tutorials/Hooks/registry.json`. The tutorials lint checks each tutorial's targets,
// signals, facts and bold words against it.

enum SupportRegistry {
    /// Bumped when the export's own shape changes (not when a vocabulary grows).
    static let schemaVersion = 3

    /// Mirrors `HeaderPaneMode`. The exhaustive switch fails to compile when a case is
    /// added there, forcing this list (and so the registry) to follow.
    static var paneModes: [String] {
        let all: [HeaderPaneMode] = [.layouts, .hub, .menu]
        return all.map { mode -> String in
            switch mode { case .layouts, .hub, .menu: return mode.rawValue }
        }
    }

    /// Mirrors `HeaderPaneDetent` (not String-backed, so named here; same compile guard).
    static var paneDetents: [String] {
        let all: [HeaderPaneDetent] = [.pane, .full]
        return all.map { d -> String in
            switch d { case .pane: return "pane"; case .full: return "full" }
        }
    }

    /// Mirrors `LayoutHubSection` directly.
    static var infoSections: [String] { LayoutHubSection.allCases.map(\.rawValue) }

    static var appVersion: String {
        Bundle.main.object(forInfoDictionaryKey: "CFBundleShortVersionString") as? String ?? "0"
    }

    /// The registry as a JSON-ready dictionary (sorted keys on encode).
    static func exportObject(version: String = appVersion) -> [String: Any] {
        let signals: [[String: Any]] = SupportSignal.allCases.filter(\.isKnown).map { s in
            var o: [String: Any] = ["id": s.rawValue, "carriesValue": s.carriesValue]
            if let t = s.targetMeaning { o["target"] = t }
            if let v = s.valueMeaning { o["value"] = v }
            return o
        }
        let facts: [[String: Any]] = SupportFact.allCases.filter(\.isKnown).map { f in
            var o: [String: Any] = ["id": f.rawValue, "type": f.valueType.rawValue,
                                    "comparators": f.comparators, "params": f.params]
            if let v = f.values { o["values"] = v }
            return o
        }
        return [
            "schema": schemaVersion,
            "version": version,
            "appVersion": version,
            // Fixed ids as strings, dynamic ids as {"pattern"}. A placeholder matches one
            // dot-free segment, except a trailing one (it takes the rest). Placeholders
            // named in `targetParams` match only the listed values.
            "targets": SupportTargets.fixed.map { $0 as Any }
                + SupportTargets.patterns.map { ["pattern": $0] as Any },
            "targetParams": SupportTargets.closedParams,
            "targetPlaces": SupportTargets.placeMap,
            "signals": signals,
            "facts": facts,
            "paneModes": paneModes,
            "paneDetents": paneDetents,
            "infoSections": infoSections,
            "labels": labels,
        ]
    }

    // MARK: Labels (tutorials spec 2.2, 2.4)

    /// The words the app shows that a tutorial step may set in bold (the tutorials lint's rule 11): every chip's
    /// title on every control's bar, every Binding card's title and choices, and per target the words drawn on it.
    /// Each list is read from the source its view draws from, so a renamed chip or card renames its label here.
    static var labels: [String: Any] {
        ["chips": chipLabels, "cards": bindingCardLabels, "targets": targetLabels]
    }

    /// Every chip title the pose's bar shows, over every control, under the base profile (a profile only hides).
    static var chipLabels: [String] {
        let profile = ControlDocLoader.profile(named: EditorProfile.base) ?? .everything
        return words(ControlDefinition.ControlType.allCases.flatMap { type in
            EditFacetBar.bar(forType: type.rawValue, profile: profile).editors.map(\.title)
        })
    }

    /// The Binding view's words: its button, each card's title (`BindingSentence`, from every doc's `io:`), and the
    /// choices on the cards (where a value comes from, where a send goes, My Data's "New value…").
    static var bindingCardLabels: [String] {
        var out: [String] = [EditKindRegistry.kind(EditKindRegistry.bindingKind)?.label].compactMap { $0 }
        for doc in ControlDocLoader.loadAll().values where !doc.io.isEmpty {
            for r in doc.io.receives {
                out.append(BindingSentence.receiveTitle(r))
                // "It comes from": each listening source in words (`DataBindingView.sourceTitle`); Nowhere is a destination's.
                out += r.from.filter { BindingSentence.method(of: $0) != nil }.map(BindingSentence.source)
            }
            for e in doc.io.emits {
                out.append(BindingSentence.title(of: e, in: doc, properties: [:]))
                out += e.whenBy.values.flatMap(\.values).filter { $0 != e.when }.map(BindingSentence.phrase)
            }
        }
        out += BindingSentence.destinations.map(BindingSentence.destination)
        out.append(WireStage.newValueLabel)
        return words(out)
    }

    /// Words on one target: the New control picker's cards (`editor.add`) and the editor's own buttons.
    static var targetLabels: [String: [String]] {
        [
            // The Add corner draws the `plus` glyph over its "Add" caption (EditorCornerButtons).
            "editor.add": words(["+", "Add"] + NewControlEntry.all().map(\.name)),
            // Try it in the pose's ⋯ menu starts Try (PoseOverflowMenu); its banner's Done ends it (TryModeControls).
            // The pose's Try chip only plays a sample (EditPoseView), so it is not this target's word.
            "editor.try": ["Done", "Try it"],
            // The pose's ⋯ (PoseOverflowMenu, "More for this control") and its Try it item, which a step rings first.
            "editor.pose.more": ["More", "Try it"],
            // The editor's Done saves (HeaderVariants).
            "editor.save": ["Done"],
        ]
    }

    /// Labels as the lint compares them: trimmed, a trailing ellipsis dropped ("New value…" is **New value**),
    /// unique and sorted.
    private static func words(_ labels: [String]) -> [String] {
        let trimmed = labels.map { l -> String in
            var w = l.trimmingCharacters(in: .whitespaces)
            while w.hasSuffix("…") || w.hasSuffix(".") { w.removeLast() }
            return w
        }
        return Array(Set(trimmed.filter { !$0.isEmpty })).sorted()
    }

    /// Pretty, key-sorted JSON so the file diffs cleanly between versions.
    static func export(version: String = appVersion) -> Data {
        (try? JSONSerialization.data(withJSONObject: exportObject(version: version),
                                     options: [.prettyPrinted, .sortedKeys])) ?? Data()
    }
}
