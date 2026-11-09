import SwiftUI
import Observation

// MARK: - AppState → signals + fact refresh (tutorials spec 2.4)
//
// One Observation loop over the handful of AppState properties that facts read or
// that signal "a screen opened". Each change: diff against the last snapshot, emit the
// transition signals (picker.open, xray.on, connection.connected, pane.open…), and ask
// the tutorial runner to look at its facts again. Emitting from here instead of from every
// button means a screen opened by ANY path (a tap, a deep link, a tutorial) reports
// itself exactly once.

/// The observed slice of app state, compared between changes.
struct SupportObservedState: Equatable {
    var picker = false
    var settings = false
    var paywall = false
    var studio = false
    var connectionPanel = false
    var templates = false
    var permissions = false
    var infoTarget: String?
    var infoSection: String?
    var xray = false
    var connected = false
    var phaseFailed = false
    var editing = false
    var paneMode: HeaderPaneMode?
    var paneFull = false
    var layoutURL: URL?
    var pinnedCount = 0
    var libraryCount = 0
    var hasPro = false
    var hasConnectPlus = false
    var founder = false
    var pipesHealthy = true
    var tabId: String?
}

extension SupportCoordinator {
    func beginObserving() {
        observed = snapshot()
        track()
    }

    private func track() {
        withObservationTracking {
            _ = snapshot()
        } onChange: { [weak self] in
            // Fires on willSet: read the new values on the next main turn.
            Task { @MainActor [weak self] in
                guard let self else { return }
                self.stateChanged()
                self.track()
            }
        }
    }

    func snapshot() -> SupportObservedState {
        var s = SupportObservedState()
        guard let app else { return s }
        s.picker = app.showingLayoutPicker
        s.settings = app.showingSettings
        s.paywall = app.showingPaywall
        s.studio = app.showingStudio
        s.connectionPanel = app.showingConnectionPanel
        s.templates = app.showingTemplateGallery
        s.permissions = app.showingPermissionsPanel
        s.infoTarget = app.layoutHubTarget.map { $0.preview.id }
        s.infoSection = infoSection?.rawValue
        s.xray = app.xRayEnabled
        s.connected = app.isConnected
        if case .failed = app.connectionPhase { s.phaseFailed = true }
        s.editing = app.inPlaceEditor != nil
        s.paneMode = headerMorph?.mode
        s.paneFull = headerMorph?.detent == .full
        s.layoutURL = app.activeLayoutURL
        s.pinnedCount = app.pinnedDeck.pinnedIds.count
        s.libraryCount = app.layoutLoader.previews.count
        s.hasPro = app.entitlements.hasProFeatures
        s.hasConnectPlus = app.entitlements.hasConnectPlus
        s.founder = isFounder
        s.pipesHealthy = Self.pipesHealthy(app.layoutPipes)
        s.tabId = app.selectedTabId
        return s
    }

    static func pipesHealthy(_ pipes: [LayoutPipe]) -> Bool {
        let h = LayoutPipe.aggregateHealth(pipes)
        return h == nil || h == .ok
    }

    private func stateChanged() {
        let old = observed ?? SupportObservedState()
        let new = snapshot()
        observed = new
        guard old != new else { return }

        func rose(_ k: KeyPath<SupportObservedState, Bool>) -> Bool { !old[keyPath: k] && new[keyPath: k] }
        func fell(_ k: KeyPath<SupportObservedState, Bool>) -> Bool { old[keyPath: k] && !new[keyPath: k] }

        if rose(\.picker) { handle(.pickerOpen) }
        if fell(\.picker) { handle(.pickerClose) }
        if rose(\.settings) { handle(.settingsOpen) }
        if rose(\.paywall) { handle(.paywallOpen) }
        if rose(\.studio) { handle(.studioOpen) }
        if rose(\.connectionPanel) { handle(.connectionOpen) }
        if rose(\.templates) { handle(.templatesOpen) }
        if rose(\.xray) { handle(.xrayOn) }
        if fell(\.xray) { handle(.xrayOff) }

        if old.infoTarget == nil, new.infoTarget != nil { handle(.infoOpen, target: new.infoSection) }
        if old.infoTarget != nil, new.infoTarget == nil { handle(.infoClose) }

        if old.paneMode != new.paneMode {
            if let m = new.paneMode {
                handle(.paneOpen, target: m.rawValue)
                if m == .hub { handle(.connectionOpen) }
            } else {
                handle(.paneClose)
            }
        }
        if new.paneMode == .layouts, old.paneFull != new.paneFull || old.paneMode != new.paneMode {
            if old.paneMode == .layouts || new.paneFull { handle(.paneDetent, target: new.paneFull ? "full" : "pane") }
        }

        if rose(\.connected) {
            handle(.connectionConnected)
            connectedAt = Date()
            scheduleStaleCheck()
        }
        if fell(\.connected) || (rose(\.phaseFailed) && !new.connected) {
            handle(.connectionDropped)
            staleCheck?.cancel(); silentLayout = nil
        }
        if old.layoutURL != new.layoutURL {
            staleCheck?.cancel(); lastIncomingAt = nil; silentLayout = nil
        }

        app?.tutorial.factsChanged()
    }

    // MARK: layout.stale

    /// Connected, bound to data, yet nothing arrived for a while: `layout.stale`.
    private func scheduleStaleCheck() {
        staleCheck?.cancel()
        let layout = app?.activeLayoutURL
        staleCheck = Task { @MainActor [weak self] in
            try? await Task.sleep(nanoseconds: 45_000_000_000)
            guard !Task.isCancelled, let self, let app = self.app,
                  app.isConnected, app.activeLayoutURL == layout,
                  let config = app.currentLayout, Self.expectsData(config) else { return }
            if let last = self.lastIncomingAt, let since = self.connectedAt, last >= since { return }
            self.silentLayout = layout
            self.handle(.layoutStale)
        }
    }

    /// Whether any control in the layout listens for data.
    static func expectsData(_ config: LayoutConfig) -> Bool {
        XRayModel.allControls(in: config).contains { !($0.sync ?? []).isEmpty }
    }

    /// The live data path landed values (AppState+Sync's flush). Cheap: not observed.
    func noteIncomingValues() {
        lastIncomingAt = Date()
        if silentLayout != nil { silentLayout = nil }
    }

    /// The open layout sat connected and silent (`layout.stale`) and nothing has arrived since: the hub pane's
    /// Not updating row (aif-6jc0k.20). Read under the pane's clock, not observed.
    var layoutSilent: Bool { silentLayout != nil && silentLayout == app?.activeLayoutURL }
}
