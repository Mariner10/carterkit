import SwiftUI
import UIKit
import CoreLocation
import UserNotifications

// MARK: - AppState → facts (tutorials spec 2.4)
//
// One switch, one line per fact. nil means "cannot read this now": the step's `expect: {fact}` does not hold
// (fail-closed). `id` is the fact's one parameter, where it has one (`SupportFact.params`).

extension SupportCoordinator {
    func fact(_ fact: SupportFact, id: String? = nil) -> JSONValue? {
        guard let app else { return nil }
        switch fact {
        case .demo:            return .bool(app.isBundledDemo || app.demoDataProvider.isRunning)
        case .layout:          return .string(app.activeLayoutId.map(Self.slug) ?? "")
        case .tab:             return selectedTabIndex.map { .number(Double($0)) }
        case .connected:       return .bool(app.isConnected)
        case .connectionKind:  return .string(connectionKind)
        // No pipes: nothing to call healthy, so a step waiting on it does not pass on an empty pane (aif-81su5).
        case .pipesHealthy:    return app.layoutPipes.isEmpty ? nil : .bool(Self.pipesHealthy(app.layoutPipes))
        case .pinned:          return .bool(app.activeLayoutId.map { app.pinnedDeck.isPinned($0) } ?? false)
        case .pinnedCount:     return .number(Double(app.pinnedDeck.pinnedIds.count))
        case .layoutCount, .libraryCount: return .number(Double(app.layoutLoader.previews.count))
        case .hasPro:          return .bool(app.entitlements.hasProFeatures)
        case .hasConnectPlus:  return .bool(app.entitlements.hasConnectPlus)
        case .tier:            return .string(tier)
        case .xray:            return .bool(app.xRayEnabled)
        case .editing:         return .bool(app.inPlaceEditor != nil)
        case .studioOpen:      return .bool(app.showingStudio)
        case .pickerOpen:      return .bool(app.showingLayoutPicker || headerMorph?.mode == .layouts)
        case .screen:          return .string(currentScreen)
        case .platform:        return .string(UIDevice.current.userInterfaceIdiom == .pad ? "ipad" : "iphone")
        case .orientation:     return .string(isLandscape ? "landscape" : "portrait")
        case .reduceMotion:    return .bool(UIAccessibility.isReduceMotionEnabled)
        case .installedDays:   return .number(Double(installedDays))
        case .launchCount:     return .number(Double(launchCount))
        case .hasTarget:       return id.map { .bool(registry.isPresent($0)) }
        case .controlExists:   return id.map { .bool(control($0) != nil) }
        case .controlType:     return id.flatMap { control($0) }.map { .string($0.type.rawValue) }
        case .controlValue:    return id.flatMap { app.controlValues[$0] }.map(Self.json)
        case .notificationsAuthorized:
            let s = app.pushManager?.authStatus
            return .bool(s == .authorized || s == .provisional || s == .ephemeral)
        case .locationAuthorized:
            let s = SupportLocationAuth.manager.authorizationStatus
            return .bool(s == .authorizedAlways || s == .authorizedWhenInUse)
        case .appVersion:      return .string(SupportRegistry.appVersion)
        case .locale:          return .string(Locale.current.language.languageCode?.identifier ?? "en")
        case .founder:         return .bool(isFounder)
        case .firstLaunch:     return .bool(isFirstLaunchSession)
        case .abBucket:        return .string(Self.abBucket)
        case .paneMode:        return .string(headerMorph?.mode?.rawValue ?? "none")
        case .paneDetent:
            guard let m = headerMorph, m.mode != nil else { return .string("") }
            return .string(m.detent == .full ? "full" : "pane")
        case .infoOpen:        return .bool(app.layoutHubTarget != nil)
        case .infoSection:     return .string(app.layoutHubTarget == nil ? "" : (infoSection?.rawValue ?? ""))
        case .layoutInLibrary: return id.map { .bool(preview($0) != nil) }
        case .layoutPinned:    return id.flatMap { preview($0) }.map { .bool(app.pinnedDeck.isPinned($0.id)) } ?? .bool(false)
        case .layoutIsCurrent:
            guard let id else { return nil }
            if id == "current" { return .bool(app.activeLayoutId != nil) }
            return .bool(app.activeLayoutId.map(Self.slug) == Self.slug(id))
        case .searchActive:    return .bool(paneSearchActive)
        case .place:
            return .string(SupportPlace.derive(editing: app.inPlaceEditor != nil, trying: app.inPlaceEditor?.isTrying ?? false,
                                               poseChip: poseChip, addSheetOpen: app.showingNewControlPicker,
                                               studioOpen: app.showingStudio, screen: currentScreen).rawValue)
        case .poseChip:        return app.inPlaceEditor == nil ? nil : .string(poseChip)
        case .addSheetOpen:    return .bool(app.showingNewControlPicker)
        case .controlCount:
            guard let config = app.currentLayout else { return nil }
            let controls = XRayModel.allControls(in: config)
            guard let id, !id.isEmpty else { return .number(Double(controls.count)) }
            return .number(Double(controls.filter { $0.type.rawValue == id }.count))
        case .selectedType:
            guard let model = app.inPlaceEditor else { return nil }
            return .string(model.selectedChildId.flatMap { model.childDict(id: $0)?["type"]?.hubString } ?? "")
        case .unknown:         return nil
        }
    }

    // MARK: Helpers

    /// The chip whose pane is open on the editor's pose (`""` none).
    var poseChip: String { app?.inPlaceEditor?.sessionController?.poseOpenFacet ?? "" }

    var selectedTabIndex: Int? {
        guard let tabs = app?.currentLayout?.tabs, !tabs.isEmpty else { return nil }
        guard let sel = app?.selectedTabId else { return 0 }
        return tabs.firstIndex { $0.id == sel } ?? 0
    }

    /// `local` | `connectPlus` | `none` for the current layout's own connection.
    var connectionKind: String {
        guard let connection = app?.currentLayout?.connection else { return "none" }
        return AppState.isConnectPlusHost(connection.url) ? "connectPlus" : "local"
    }

    var tier: String {
        guard let app else { return "free" }
        if let t = app.connectServerGrant?.tier ?? app.activeConnectTierID { return Self.shortTier(t) }
        if app.entitlements.hasConnectPlus { return "connectPlus" }
        return app.entitlements.hasProFeatures ? "pro" : "free"
    }

    /// `CARTER.connectplus.duo` → `duo`.
    static func shortTier(_ raw: String) -> String {
        raw.split(separator: ".").last.map(String.init) ?? raw
    }

    /// What is on top right now, most specific first.
    var currentScreen: String {
        guard let app else { return "none" }
        if app.showingFirstRun { return "landing" }
        if app.inPlaceEditor != nil { return "editor" }
        if app.showingStudio { return "studio" }
        if app.showingTemplateGallery { return "templates" }
        if app.layoutHubTarget != nil { return "info" }
        if app.showingSettings { return "settings" }
        if app.showingPaywall { return "paywall" }
        if app.showingPermissionsPanel { return "permissions" }
        if app.showingConnectionPanel { return "connection" }
        if app.showingLayoutPicker { return "picker" }
        if app.showingIndexGuide || app.activeMarkdownSheet != nil { return "controls" }
        if headerMorph?.mode != nil { return "pane" }
        if app.xRayEnabled { return "xray" }
        return "canvas"
    }

    private var isLandscape: Bool {
        let scene = UIApplication.shared.connectedScenes.compactMap { $0 as? UIWindowScene }.first
        return scene?.effectiveGeometry.interfaceOrientation.isLandscape ?? false
    }

    var installedDays: Int {
        Calendar.current.dateComponents([.day], from: installDate, to: Date()).day ?? 0
    }

    func control(_ id: String) -> ControlDefinition? {
        guard let config = app?.currentLayout else { return nil }
        let bare = id.hasPrefix("control.") ? String(id.dropFirst(8)) : id
        return XRayModel.allControls(in: config).first { $0.id == bare }
    }

    /// A library layout by slug (`first-layout`) or file name (`first-layout.json`).
    func preview(_ id: String) -> LayoutPreview? {
        guard let app else { return nil }
        if id == "current" { return app.currentLayoutPreview() }
        let want = Self.slug(id)
        return app.layoutLoader.previews.first { Self.slug($0.id) == want }
    }

    nonisolated static func json(_ v: ControlValue) -> JSONValue {
        switch v {
        case .bool(let b): return .bool(b)
        case .number(let n): return .number(n)
        case .string(let s): return .string(s)
        }
    }

    /// Stable per install (spec §9.5).
    static var abBucket: String {
        let key = "carter.support.abBucket"
        if let b = UserDefaults.standard.string(forKey: key) { return b }
        let b = Bool.random() ? "a" : "b"
        UserDefaults.standard.set(b, forKey: key)
        return b
    }
}

/// One shared manager for reading location authorization (creating a
/// `CLLocationManager` per fact evaluation is expensive). Only its status is read.
@MainActor
enum SupportLocationAuth {
    static let manager = CLLocationManager()
}

// MARK: - Place (tutorial context spec 1.1)

/// Where the app is, coarsely, in the words a person uses. A pure function over six reads, so it tests without a screen.
enum SupportPlace: String, CaseIterable, Sendable {
    case landing, canvas, studio, editor, pose, `try`, other

    /// Order: landing (the first-run feed is a cover over everything), try, pose, editor, studio, canvas, other. The layout picker and the header pane count as the canvas.
    static func derive(editing: Bool, trying: Bool, poseChip: String, addSheetOpen: Bool,
                       studioOpen: Bool, screen: String) -> SupportPlace {
        if screen == "landing" { return .landing }
        if editing {
            if trying { return .`try` }
            if !poseChip.isEmpty || addSheetOpen { return .pose }
            return .editor
        }
        if studioOpen { return .studio }
        return ["canvas", "picker", "pane"].contains(screen) ? .canvas : .other
    }
}
