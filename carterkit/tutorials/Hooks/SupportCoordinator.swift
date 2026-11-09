import SwiftUI
import Observation

// MARK: - The tutorials' hooks, bound to AppState (tutorials spec 2.4)
//
// Facts (`SupportFacts.swift`), the window-level `SupportTargetRegistry`, signals (`SupportSignals.swift`), and the
// observation loop that turns AppState changes into signals and fact refreshes (`SupportObservation.swift`). It also
// carries what the window overlay draws for the app: a toast and target highlights (`SupportAppOverlay`).
// The guide engine, its feed and its triggers are gone (aif-6jc0k.12): the tutorial runner is the one consumer.
//
// Inert until `start()` runs at launch, so the throwaway AppStates used by previews and the unit suite never observe.

@MainActor
@Observable
final class SupportCoordinator {
    struct Toast: Identifiable, Equatable {
        let id = UUID()
        let md: String
    }

    /// One pending scroll-into-view request.
    struct ScrollRequest: Equatable {
        let target: String
        let token: UUID
    }

    @ObservationIgnored weak var app: AppState?
    let registry: SupportTargetRegistry

    // MARK: UI state the host views read

    private(set) var toast: Toast?
    /// Targets pulsing without a card (`highlight`, `highlightLayout`), with their end time.
    private(set) var highlights: [String: Date] = [:]
    /// A `settings.section` request for the Settings sheet to honour, then clear.
    var settingsFocus: String?
    /// A `pane` search prefill for the layouts pane to take, then clear.
    var paneQuery: String?
    /// The layouts pane's search field has text or focus (fact `searchActive`).
    var paneSearchActive = false
    /// `info.section` request for an open Layout Info sheet.
    var infoSectionRequest: LayoutHubSection?
    /// The section the open Layout Info sheet shows (fact `infoSection`).
    var infoSection: LayoutHubSection?
    /// A template card the gallery should bring forward (`template(id)`).
    var templateFocus: String?
    private(set) var scrollRequest: ScrollRequest?

    // MARK: Bookkeeping (not observed)

    /// The header's morph engine, attached by the container (observed, so the fact
    /// loop starts tracking the pane the moment it exists).
    var headerMorph: HeaderMorphCoordinator?
    @ObservationIgnored var reduceMotion = false
    @ObservationIgnored private(set) var started = false
    @ObservationIgnored private(set) var isFirstLaunchSession = false
    @ObservationIgnored var lastIncomingAt: Date?
    @ObservationIgnored var connectedAt: Date?
    @ObservationIgnored var staleCheck: Task<Void, Never>?
    /// The layout `layout.stale` fired for, until values arrive, the link drops or another layout opens.
    @ObservationIgnored var silentLayout: URL?
    @ObservationIgnored var toastTask: Task<Void, Never>?
    @ObservationIgnored var observed: SupportObservedState?
    @ObservationIgnored var launchCount = 0
    @ObservationIgnored lazy var installDate: Date = Self.resolveInstallDate()

    init(app: AppState, registry: SupportTargetRegistry = .shared) {
        self.app = app
        self.registry = registry
    }

    /// The started coordinator (the app's). Sandbox/preview AppStates never start one.
    static weak var active: SupportCoordinator?

    /// Whether grid controls should publish `control.<id>` targets right now: only
    /// while a tutorial runs, target labels are on, or something is highlighted — so an
    /// idle app never pays for per-control frame tracking.
    ///
    /// Control bodies read ONLY the stored `tracksControlTargets`, which flips when
    /// tracking starts/stops — never the runner's per-step state, so a tutorial step
    /// does not re-run every control body.
    static func tracksControls(of app: AppState) -> Bool {
        guard let c = active, c.app === app else { return false }
        return c.tracksControlTargets
    }

    /// Stored mirror of "a tutorial runs, target labels are on, or something is
    /// highlighted". Written only when the value changes.
    private(set) var tracksControlTargets = false

    private var wantsControlTargets: Bool {
        (app?.tutorial.isActive ?? false) || registry.showsLabels || !highlights.isEmpty
    }

    /// Keep `tracksControlTargets` in step with its inputs (Observation loop).
    func observeTracking() {
        let now = withObservationTracking { wantsControlTargets } onChange: { [weak self] in
            Task { @MainActor [weak self] in self?.observeTracking() }
        }
        if now != tracksControlTargets { tracksControlTargets = now }
    }

    /// Anything the overlay window draws right now (it is hidden otherwise).
    var overlayActive: Bool {
        toast != nil || !highlights.isEmpty || registry.showsLabels
            // The tutorial card, ring and pill float over sheets from this window (aif-6jc0k.23).
            || (app.map { $0.tutorial.phase != .idle } ?? false)
            // The local-write Undo toast lives in this window too (m7s.20 / 73q2.40): without
            // this the window stayed hidden and the toast never showed.
            || app?.localUndo != nil
            // The app-drawn confirmation (aif-3618x.4) is drawn here as well.
            || app?.hubPrompts.current != nil
            || app?.hubToasts.current != nil
            // So is an expanded group (aif-3618x.5), until its collapse lands.
            || app?.expandSheets.current != nil || app?.expandSheets.hiddenKey != nil
            // And hubs' progress tasks (aif-qs8b0.19): the pill, the tray, the progress sheet.
            || !(app?.hubTasks.visible.isEmpty ?? true) || app?.hubTasks.sheetKey != nil
            // The log console sheet (aif-qs8b0.21).
            || app?.hubLogs.sheetKey != nil
    }

    // MARK: Founder

    /// The relay grant's founder flag — never a Debug flag, except the
    /// Debug-only `AUTO_FOUNDER=1` screenshot override.
    var isFounder: Bool {
        #if DEBUG
        if ProcessInfo.processInfo.environment["AUTO_FOUNDER"] == "1" { return true }
        #endif
        return app?.connectServerGrant?.founder == true
    }

    // MARK: Launch

    /// The one launch-time step, next to `AppFeedStore.shared.start()`.
    func start() {
        guard !started, app != nil else { return }
        started = true
        Self.active = self
        registry.aliasResolver = { [weak self] id in self?.alias(id) }
        launchCount = UserDefaults.standard.integer(forKey: Self.launchCountKey) + 1
        UserDefaults.standard.set(launchCount, forKey: Self.launchCountKey)
        _ = installDate
        beginObserving()
        observeTracking()
    }

    static let launchCountKey = "carter.support.launchCount"
    private static var launchSignalsSent = false

    /// A first launch (the first run's gate, `AppState+FirstRun`, or the founder's "Run first open now") counts as
    /// one for facts.
    func markFirstLaunchSession() { isFirstLaunchSession = true }

    /// Fire `app.launch` once the launch layout is settled (called by the app after its launch routing). The first
    /// launch is the first run's (`AppState+FirstRun`).
    func launchSignals() {
        // Every iPad window's root runs this `onAppear`: the launch happens once.
        guard started, !Self.launchSignalsSent else { return }
        Self.launchSignalsSent = true
        Task { @MainActor in
            handle(.appLaunch, target: nil, value: nil)
            let days = Calendar.current.dateComponents([.day], from: installDate, to: Date()).day ?? 0
            handle(.appInstalledDays, target: nil, value: .number(Double(days)))
        }
    }

    // MARK: Toast / highlight / scroll

    func showToast(_ md: String, seconds: Double) {
        let t = Toast(md: md)
        toast = t
        toastTask?.cancel()
        toastTask = Task { @MainActor [weak self] in
            try? await Task.sleep(nanoseconds: UInt64(max(1, min(seconds, 10)) * 1_000_000_000))
            guard !Task.isCancelled, self?.toast?.id == t.id else { return }
            self?.toast = nil
        }
    }

    func highlight(_ target: String, seconds: Double) {
        let key = registry.resolve(target)
        highlights[key] = Date().addingTimeInterval(max(0.5, min(seconds, 10)))
        Task { @MainActor [weak self] in
            try? await Task.sleep(nanoseconds: UInt64(max(0.5, min(seconds, 10)) * 1_000_000_000))
            guard let self, let until = self.highlights[key], until <= Date() else { return }
            self.highlights[key] = nil
        }
    }

    func requestScroll(to target: String) {
        scrollRequest = ScrollRequest(target: registry.resolve(target), token: UUID())
    }

    // MARK: Target aliases

    private func alias(_ id: String) -> String? {
        switch id {
        case "pane.row.current":
            return app?.activeLayoutId.map { "pane.row.\(Self.slug($0))" }
        default:
            return nil
        }
    }

    /// A library layout's target/fact id: the file name without its extension.
    nonisolated static func slug(_ previewID: String) -> String {
        previewID.hasSuffix(".json") ? String(previewID.dropLast(5)) : previewID
    }

    // MARK: Install age

    private static func resolveInstallDate() -> Date {
        let key = "carter.support.installedAt"
        if let d = UserDefaults.standard.object(forKey: key) as? Date { return d }
        // The Documents folder is created on first run: the best install date an
        // existing install has.
        let docs = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask).first
        let created = docs.flatMap { try? FileManager.default.attributesOfItem(atPath: $0.path)[.creationDate] as? Date }
        let d = created ?? Date()
        UserDefaults.standard.set(d, forKey: key)
        return d
    }
}
