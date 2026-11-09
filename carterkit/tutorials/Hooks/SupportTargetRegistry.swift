import SwiftUI
import UIKit
import Observation

// MARK: - Window-level target registry (tutorials spec 2.4)
//
// Views publish their GLOBAL frame under a registry id with `.supportTarget("…")`.
// No anchor preferences: those do not cross UIKit-hosted TabView / sheet boundaries,
// which is what made the old two-host overlay flicker. Every registration carries an
// owner token, so when a sheet holding `picker.search` is dismissed while another
// live view also publishes `picker.search`, the dismissed one only removes itself.

@MainActor
@Observable
final class SupportTargetRegistry {
    static let shared = SupportTargetRegistry()

    struct Entry: Equatable {
        var owner: UUID
        var frame: CGRect
        var registeredAt: Date
        /// The window scene the registering view lives in (nil: unknown ⇒ any scene).
        var scene: ObjectIdentifier? = nil
        /// Registered from inside a presentation (sheet/cover content, or a pushed
        /// navigation destination — `\.isPresented`). Root content is false.
        var inPresentation = false
    }

    /// id → registrations, newest last. The newest live registration wins. NOT
    /// observed: views re-render off the coarse `version` instead, so per-frame
    /// geometry writes during scrolling never invalidate anything directly.
    @ObservationIgnored private(set) var entries: [String: [Entry]] = [:]

    /// Bumped (at most once per main-loop turn) when a registration appears,
    /// disappears, or moves by a point or more. Overlay views read it.
    private(set) var version = 0
    @ObservationIgnored private var bumpPending = false

    /// How many overlay views (tutorial ring/card, highlight rings, target-id labels)
    /// are on screen and need to follow a MOVING target. While 0, a registration that
    /// only moves (a chip scrolling) writes its frame but bumps nothing: `frame(_:)`
    /// reads the entries live, and `beginLive()` bumps once to refresh.
    @ObservationIgnored private var liveDemand = 0

    func beginLive() {
        liveDemand += 1
        if liveDemand == 1 { bumpVersion() }
    }
    func endLive() { liveDemand = max(0, liveDemand - 1) }

    /// Alias resolver (e.g. `pane.row.current` → `pane.row.<layoutId>`). WP3 sets it.
    /// Return nil when the id is not an alias.
    @ObservationIgnored var aliasResolver: (@MainActor (String) -> String?)?

    /// The scene whose window is key (iPad multi-window): its registrations win.
    /// Set by the overlay installer; nil ⇒ every scene counts.
    @ObservationIgnored var activeScene: ObjectIdentifier?

    /// The visible window bounds (global coordinates). A target must show at least
    /// 30 % of its area, or a 44×44 pt piece, inside them to count as present. nil ⇒
    /// no clipping check.
    @ObservationIgnored var visibleBounds: CGRect?

    /// Whether a full-screen cover is up over the app window. When true, targets
    /// registered by root (non-presented) content count as absent. Injectable.
    @ObservationIgnored var coverProbe: @MainActor () -> Bool = { SupportTargetRegistry.appWindowShowsFullScreenCover() }

    /// Founder "Show target ids" (spec §18): draw every registered id on screen.
    var showsLabels = false

    init() {}

    // MARK: Registration

    func register(_ id: String, owner: UUID, frame: CGRect, scene: ObjectIdentifier? = nil, inPresentation: Bool = false) {
        var list = entries[id] ?? []
        if let i = list.firstIndex(where: { $0.owner == owner }) {
            let old = list[i]
            guard old.frame != frame || old.scene != scene || old.inPresentation != inPresentation else { return }
            list[i].frame = frame
            list[i].scene = scene
            list[i].inPresentation = inPresentation
            entries[id] = list
            if (liveDemand > 0 && Self.movedNoticeably(old.frame, frame)) || old.scene != scene || old.inPresentation != inPresentation {
                bumpVersion()
            }
        } else {
            list.append(Entry(owner: owner, frame: frame, registeredAt: Date(), scene: scene, inPresentation: inPresentation))
            entries[id] = list
            bumpVersion()
        }
    }

    /// Remove only this owner's registration of `id`.
    func unregister(_ id: String, owner: UUID) {
        guard var list = entries[id] else { return }
        let before = list.count
        list.removeAll { $0.owner == owner }
        entries[id] = list.isEmpty ? nil : list
        if list.count != before { bumpVersion() }
    }

    private static func movedNoticeably(_ a: CGRect, _ b: CGRect) -> Bool {
        abs(a.minX - b.minX) >= 1 || abs(a.minY - b.minY) >= 1
            || abs(a.width - b.width) >= 1 || abs(a.height - b.height) >= 1
    }

    private func bumpVersion() {
        guard !bumpPending else { return }
        bumpPending = true
        DispatchQueue.main.async { [weak self] in
            MainActor.assumeIsolated {
                guard let self else { return }
                self.bumpPending = false
                self.version &+= 1
            }
        }
    }

    // MARK: Lookup

    /// The id after alias resolution.
    func resolve(_ id: String) -> String {
        if entries[id] != nil { return id }
        return aliasResolver?(id) ?? id
    }

    /// The target's global frame (newest usable registration in the active scene),
    /// after alias resolution. Reading it subscribes the caller to `version`.
    ///
    /// Present means: a usable rect, in the key window's scene, at least partly
    /// on screen (see `visibleBounds`), and not root content under a full-screen
    /// cover. Not caught: occlusion by a non-full-screen sheet or popover, by another
    /// view in the same layer, by a cover over a sheet (content inside the sheet
    /// counts as presented), and root content of a pushed navigation destination
    /// under a cover (it reads as presented).
    func frame(_ id: String) -> CGRect? {
        _ = version
        let key = resolve(id)
        guard let list = entries[key] else { return nil }
        let covered = list.contains { !$0.inPresentation } ? coverProbe() : false
        for e in list.reversed() {
            if let s = e.scene, let active = activeScene, s != active { continue }
            if covered, !e.inPresentation { continue }
            guard Self.isUsable(e.frame), Self.isVisible(e.frame, in: visibleBounds) else { continue }
            return e.frame
        }
        return nil
    }

    func isPresent(_ id: String) -> Bool { frame(id) != nil }

    var registeredIDs: [String] {
        _ = version
        return entries.keys.sorted()
    }

    /// A zero-size or off-infinity frame is "not on screen".
    nonisolated static func isUsable(_ r: CGRect) -> Bool {
        !r.isNull && !r.isInfinite && r.width > 0.5 && r.height > 0.5
            && r.origin.x.isFinite && r.origin.y.isFinite
    }

    /// Enough of `r` inside `bounds`: ≥ 30 % of its area, or a 44×44 pt piece.
    nonisolated static func isVisible(_ r: CGRect, in bounds: CGRect?) -> Bool {
        guard let bounds, isUsable(bounds) else { return true }
        let v = r.intersection(bounds)
        guard !v.isNull, v.width > 0, v.height > 0 else { return false }
        if v.width * v.height >= 0.3 * r.width * r.height { return true }
        return v.width >= 44 && v.height >= 44
    }

    /// A full-screen (or over-full-screen) presentation is up in a visible app window.
    static func appWindowShowsFullScreenCover() -> Bool {
        let windows = UIApplication.shared.connectedScenes
            .compactMap { $0 as? UIWindowScene }
            .flatMap(\.windows)
            .filter { !($0 is SupportOverlayWindow) && !$0.isHidden }
        for w in windows {
            var vc = w.rootViewController?.presentedViewController
            while let p = vc {
                if !p.isBeingDismissed, p.modalPresentationStyle == .fullScreen || p.modalPresentationStyle == .overFullScreen {
                    return true
                }
                vc = p.presentedViewController
            }
        }
        return false
    }
}

// MARK: - The modifier

private struct SupportSceneIDKey: EnvironmentKey { static let defaultValue: ObjectIdentifier? = nil }
extension EnvironmentValues {
    /// The window scene this view hierarchy belongs to (set by the overlay host).
    var supportSceneID: ObjectIdentifier? {
        get { self[SupportSceneIDKey.self] }
        set { self[SupportSceneIDKey.self] = newValue }
    }
}

private final class LastFrame { var frame: CGRect = .null }

private struct SupportTargetModifier: ViewModifier {
    let id: String
    var registry: SupportTargetRegistry
    @State private var owner = UUID()
    /// Not @State: a write per scroll frame would re-evaluate this body (and the
    /// geometry reader) for every chip. A plain box changes nothing SwiftUI watches.
    @State private var last = LastFrame()
    @Environment(\.supportSceneID) private var sceneID
    @Environment(\.isPresented) private var isPresented

    func body(content: Content) -> some View {
        content.background {
            GeometryReader { proxy in
                let frame = proxy.frame(in: .global)
                Color.clear
                    .onAppear { last.frame = frame; register(id, frame) }
                    .onChange(of: frame) { _, f in last.frame = f; register(id, f) }
                    .onDisappear { registry.unregister(id, owner: owner) }
            }
        }
        .onChange(of: id) { old, new in
            registry.unregister(old, owner: owner)
            // Register the new id at once; the geometry may not change for a while.
            if !last.frame.isNull { register(new, last.frame) }
        }
    }

    private func register(_ id: String, _ frame: CGRect) {
        registry.register(id, owner: owner, frame: frame, scene: sceneID, inPresentation: isPresented)
    }
}

extension View {
    /// Publish this view as a Support target (spec §7.1). Ids are namespaced:
    /// `header.connection`, `control.<id>`, `pane.row.<layoutId>`, …
    @MainActor func supportTarget(_ id: String, registry: SupportTargetRegistry? = nil) -> some View {
        modifier(SupportTargetModifier(id: id, registry: registry ?? .shared))
    }
}

extension View {
    /// Mark this overlay as needing live target frames (see `SupportTargetRegistry.beginLive`).
    @MainActor func needsLiveTargetFrames(_ registry: SupportTargetRegistry = .shared) -> some View {
        onAppear { registry.beginLive() }.onDisappear { registry.endLive() }
    }
}

// MARK: - "Show target ids" overlay (spec §18)

/// Draws every registered id at its frame. Place it in window coordinates
/// (`SupportOverlayHost` does this when `registry.showsLabels` is on).
struct SupportTargetLabels: View {
    var registry: SupportTargetRegistry = .shared

    var body: some View {
        GeometryReader { proxy in
            let origin = proxy.frame(in: .global).origin
            ZStack(alignment: .topLeading) {
                ForEach(registry.registeredIDs, id: \.self) { id in
                    if let r = registry.frame(id) {
                        let local = r.offsetBy(dx: -origin.x, dy: -origin.y)
                        Rectangle()
                            .strokeBorder(Color.orange.opacity(0.8), style: StrokeStyle(lineWidth: 1, dash: [4, 3]))
                            .frame(width: local.width, height: local.height)
                            .offset(x: local.minX, y: local.minY)
                        Text(id)
                            .font(.system(size: 9, weight: .semibold, design: .monospaced))
                            .foregroundStyle(.white)
                            .padding(.horizontal, 3)
                            .background(Color.orange.opacity(0.85), in: RoundedRectangle(cornerRadius: 3))
                            .fixedSize()
                            .offset(x: local.minX, y: max(0, local.minY - 12))
                    }
                }
            }
            .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .topLeading)
        }
        .allowsHitTesting(false)
        .ignoresSafeArea()
        .needsLiveTargetFrames(registry)
    }
}
