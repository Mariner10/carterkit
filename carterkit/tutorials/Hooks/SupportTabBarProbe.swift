import SwiftUI
import UIKit

// MARK: - Tab bar targets (spec §7.1: `header.tabs`, `canvas.tab.<n>`)
//
// The layout's tabs live in a UIKit tab bar SwiftUI never exposes a frame for. While a
// tutorial needs targets, this probe finds the window's visible `UITabBar`, registers its
// frame as `header.tabs` and each item's button as `canvas.tab.<n>` (left to right),
// and refreshes twice a second so rotation and bar hiding follow.

struct SupportTabBarProbe: UIViewRepresentable {
    var count: Int
    var registry: SupportTargetRegistry = .shared

    final class Probe: UIView {
        var count = 0
        var registry: SupportTargetRegistry?
        private let owner = UUID()
        private var timer: Timer?
        private var registered: Set<String> = []

        override func didMoveToWindow() {
            super.didMoveToWindow()
            timer?.invalidate()
            guard window != nil else { clear(); return }
            refresh()
            timer = Timer.scheduledTimer(withTimeInterval: 0.5, repeats: true) { [weak self] _ in
                MainActor.assumeIsolated { self?.refresh() }
            }
        }

        func refresh() {
            guard let window, let registry else { return }
            guard let bar = Self.tabBar(in: window), !bar.isHidden, bar.alpha > 0.01 else { clear(); return }
            var ids: Set<String> = []
            let barFrame = bar.convert(bar.bounds, to: nil)
            let scene = window.windowScene.map(ObjectIdentifier.init)
            registry.register("header.tabs", owner: owner, frame: barFrame, scene: scene)
            ids.insert("header.tabs")
            let buttons = bar.subviews.flatMap { Self.controls(in: $0) }
                .map { $0.convert($0.bounds, to: nil) }
                .filter { $0.width > 10 && $0.height > 10 && barFrame.intersects($0) }
                .sorted { $0.minX < $1.minX }
            for (i, frame) in buttons.prefix(count).enumerated() {
                registry.register("canvas.tab.\(i)", owner: owner, frame: frame, scene: scene)
                ids.insert("canvas.tab.\(i)")
            }
            for stale in registered.subtracting(ids) { registry.unregister(stale, owner: owner) }
            registered = ids
        }

        func clear() {
            for id in registered { registry?.unregister(id, owner: owner) }
            registered = []
        }

        deinit {
            timer?.invalidate()
            let ids = registered, owner = owner, registry = registry
            DispatchQueue.main.async {
                MainActor.assumeIsolated { for id in ids { registry?.unregister(id, owner: owner) } }
            }
        }

        static func tabBar(in view: UIView) -> UITabBar? {
            if let bar = view as? UITabBar, bar.window != nil { return bar }
            for sub in view.subviews { if let bar = tabBar(in: sub) { return bar } }
            return nil
        }

        /// The bar's item buttons: its tappable controls (class names vary by OS).
        static func controls(in view: UIView) -> [UIView] {
            if view is UIControl { return [view] }
            return view.subviews.flatMap { controls(in: $0) }
        }
    }

    func makeUIView(context: Context) -> Probe {
        let p = Probe()
        p.isUserInteractionEnabled = false
        p.count = count
        p.registry = registry
        return p
    }

    func updateUIView(_ p: Probe, context: Context) {
        p.count = count
        p.refresh()
    }

    static func dismantleUIView(_ p: Probe, coordinator: ()) {
        MainActor.assumeIsolated { p.clear() }
    }
}
