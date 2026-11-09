import SwiftUI
import UIKit

// MARK: - Signals (tutorials spec 2.4)
//
// `AppState.signal(_:target:value:)` is the one emit point every site calls. It forwards to the tutorial runner, whose
// doing step checks when the signal meets its `expect`.

extension AppState {
    /// Report that something just happened. Safe to call from any site, any time: a no-op in preview renders.
    func signal(_ signal: SupportSignal, target: String? = nil, value: JSONValue? = nil) {
        guard !isPreviewRender else { return }
        if Thread.isMainThread {
            MainActor.assumeIsolated { self.tutorial.handle(signal, target: target, value: value) }
        } else {
            DispatchQueue.main.async { self.signal(signal, target: target, value: value) }
        }
    }

    /// `control.appeared` once per control type in a freshly loaded layout.
    func signalControlsAppeared(_ config: LayoutConfig) {
        let types = Set(XRayModel.allControls(in: config).map(\.type.rawValue))
        for t in types.sorted() { signal(.controlAppeared, target: t) }
    }
}

extension SupportCoordinator {
    /// A signal from the observation loop or chrome holding the coordinator (`launchSignals`, the header panes):
    /// the tutorial runner hears it as it hears `AppState.signal`. A no-op until `start()`.
    func handle(_ s: SupportSignal, target: String? = nil, value: JSONValue? = nil) {
        guard started, let app else { return }
        app.tutorial.handle(s, target: target, value: value)
    }
}

extension AppState {
    /// The live data path delivered values: `layout.stale` stands down.
    func supportNoteIncomingValues() {
        guard Thread.isMainThread else { return }
        MainActor.assumeIsolated { support.noteIncomingValues() }
    }
}
