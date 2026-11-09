import Foundation

// MARK: - The hooks registry: what a tutorial can bind to (tutorials spec 2.4)
//
// Three closed vocabularies (targets, signals, facts). Each is a Swift enum here; `SupportRegistry.export()` writes
// them to `Tutorials/Hooks/registry.json` so `scripts/tutorials-lint.py` can prove a tutorial only names things this
// build has. Adding a case here is the whole "teach tutorials something new" step; the export and lint follow.

/// Things the app emits, that a tutorial step's `expect: {signal}` can listen for.
enum SupportSignal: String, CaseIterable {
    case appLaunch = "app.launch", appFirstLaunch = "app.firstLaunch"
    case appForeground = "app.foreground", appInstalledDays = "app.installedDays"
    case layoutLoaded = "layout.loaded", layoutLoadFailed = "layout.loadFailed"
    case layoutStale = "layout.stale", layoutPinned = "layout.pinned"
    case layoutShared = "layout.shared", layoutImported = "layout.imported"
    case tabSwitch = "tab.switch"
    case controlInteract = "control.interact", controlAppeared = "control.appeared"
    case controlValueChanged = "control.valueChanged"
    case pickerOpen = "picker.open", pickerClose = "picker.close"
    case templatesOpen = "templates.open", templateLoaded = "template.loaded"
    case studioOpen = "studio.open", studioCreate = "studio.create"
    case studioClaude = "studio.claude", studioConnect = "studio.connect"
    case editorCreated = "editor.created", editorSelect = "editor.select"
    case editorAdd = "editor.add", editorAttributes = "editor.attributes"
    case editorChange = "editor.change", editorSave = "editor.save", editorDiscard = "editor.discard"
    case editorChoose = "editor.choose", editorAddSheetOpen = "editor.addSheet.open",
         editorAddIntent = "editor.addIntent"
    // The tutorials' pose signals (aif-6jc0k.5, tutorials spec 2.4): a chip opened, the Binding view opened, Try began.
    case editorChip = "editor.chip", editorBinding = "editor.binding", editorTry = "editor.try"
    case entryOpen = "entry.open", entryBrowse = "entry.browse"
    case entryAdd = "entry.add", entryEdit = "entry.edit", entryDelete = "entry.delete"
    case entryUndo = "entry.undo", entryRestore = "entry.restore"
    case connectionOpen = "connection.open", connectionConnected = "connection.connected"
    case connectionDropped = "connection.dropped", connectionPaired = "connection.paired"
    case connectionQRScanned = "connection.qrScanned"
    case xrayOn = "xray.on", xrayOff = "xray.off", xrayInspect = "xray.inspect"
    case settingsOpen = "settings.open", supportOpen = "support.open"
    case paywallOpen = "paywall.open", purchaseCompleted = "purchase.completed"
    case glanceTapped = "glance.tapped", notificationOpened = "notification.opened"
    case deeplinkOpened = "deeplink.opened"
    // §19.2
    case paneOpen = "pane.open", paneClose = "pane.close", paneDetent = "pane.detent"
    case paneSearch = "pane.search", paneLayoutSelected = "pane.layout.selected"
    case paneLayoutPinned = "pane.layout.pinned", paneLayoutUnpinned = "pane.layout.unpinned"
    case paneLayoutReordered = "pane.layout.reordered", paneRowMenu = "pane.row.menu"
    case paneAction = "pane.action", menuRow = "menu.row"
    case infoOpen = "info.open", infoSection = "info.section", infoClose = "info.close"
    case infoApply = "info.apply", infoRename = "info.rename", infoDelete = "info.delete"
    case unknown

    var isKnown: Bool { self != .unknown }

    /// What the signal's `target` payload carries, or nil when it carries none.
    var targetMeaning: String? {
        switch self {
        case .layoutLoaded: return "layout name"
        case .tabSwitch: return "tab index"
        case .controlInteract, .controlValueChanged, .editorSelect, .xrayInspect: return "control.<id>"
        case .controlAppeared, .editorAdd: return "control type"
        case .templateLoaded: return "template id"
        case .editorChange: return "field"
        case .editorChip: return "chip"
        case .editorChoose: return "stage choice id"
        case .editorAddIntent: return "intent"
        case .entryBrowse, .entryAdd, .entryEdit, .entryDelete, .entryUndo, .entryRestore: return "collection"
        case .entryOpen: return "collection[:entry id]"
        case .purchaseCompleted: return "product id"
        case .deeplinkOpened: return "host"
        case .paneOpen: return "layouts|hub|menu"
        case .paneDetent: return "pane|full"
        case .paneSearch: return "query"
        case .paneLayoutSelected, .paneLayoutPinned, .paneRowMenu: return "layout id"
        case .paneAction: return "studio|templates|scan"
        case .menuRow: return "menu row id"
        case .infoOpen, .infoSection: return "section"
        default: return nil
        }
    }

    /// Signals whose payload has a value a `wait.match` can compare.
    var carriesValue: Bool { self == .controlValueChanged || self == .appInstalledDays || self == .editorChange }

    /// What the signal's `value` payload carries, for the registry export (nil: none).
    var valueMeaning: String? {
        switch self {
        case .controlValueChanged: return "the control's value"
        case .appInstalledDays: return "days"
        case .editorChange: return "the field's new value (none: removed)"
        case .editorAdd: return "{control: <the new control's id>}"
        default: return nil
        }
    }

    /// `editor.add`'s value: the new control's id, which a tutorial step's `as:` keeps (tutorials spec 2.3, Slots).
    static func added(control id: String) -> JSONValue { .object(["control": .string(id)]) }
}

/// What a fact's value is, for the lint and the comparator check.
enum SupportFactValueType: String, Sendable { case bool, number, string, version }

/// Things a tutorial step's `expect: {fact}` can read.
enum SupportFact: String, CaseIterable {
    case demo, layout, tab, connected, connectionKind, pipesHealthy, pinned, pinnedCount
    case layoutCount, hasPro, hasConnectPlus, tier, xray, editing, studioOpen, pickerOpen
    case screen, platform, orientation, reduceMotion, installedDays, launchCount
    case hasTarget, controlExists, controlType, controlValue
    case notificationsAuthorized, locationAuthorized, appVersion, locale, founder
    case firstLaunch, abBucket
    // §19.4
    case paneMode, paneDetent, infoOpen, infoSection, layoutInLibrary, layoutPinned
    case layoutIsCurrent, libraryCount, searchActive
    // Where you are (tutorial context spec 1.1, 1.2)
    case place, poseChip, addSheetOpen, controlCount, selectedType
    case unknown

    var isKnown: Bool { self != .unknown }

    var valueType: SupportFactValueType {
        switch self {
        case .pinnedCount, .layoutCount, .installedDays, .launchCount, .libraryCount, .tab, .controlCount: return .number
        case .appVersion: return .version
        case .layout, .connectionKind, .tier, .screen, .platform, .orientation, .locale,
             .abBucket, .paneMode, .paneDetent, .infoSection, .controlType, .place, .poseChip, .selectedType:
            return .string
        case .controlValue: return .string   // any JSON scalar; numbers compare numerically
        default: return .bool
        }
    }

    /// Comparators the lint accepts. `truthy` = the bare `{"fact": x}` form.
    var comparators: [String] {
        switch valueType {
        case .bool: return ["truthy"]
        case .number: return ["truthy", "is", "isNot", "gte", "lte"]
        case .version: return ["is", "isNot", "gte", "lte"]
        case .string:
            return self == .controlValue ? ["truthy", "is", "isNot", "gte", "lte"] : ["truthy", "is", "isNot"]
        }
    }

    /// Named parameters the fact reads (required first).
    var params: [String] {
        switch self {
        case .hasTarget: return ["target"]
        case .controlExists, .controlType, .controlValue: return ["id"]
        case .layoutInLibrary, .layoutPinned, .layoutIsCurrent: return ["id"]
        case .controlCount: return ["id"]   // a control type; empty counts all
        default: return []
        }
    }

    /// Closed value sets, where the fact has one.
    var values: [String]? {
        switch self {
        case .connectionKind: return ["local", "connectPlus", "none"]
        case .platform: return ["iphone", "ipad"]
        case .orientation: return ["portrait", "landscape"]
        case .abBucket: return ["a", "b"]
        case .paneMode: return ["none"] + SupportRegistry.paneModes
        case .paneDetent: return SupportRegistry.paneDetents
        case .infoSection: return SupportRegistry.infoSections
        case .place: return SupportPlace.allCases.map(\.rawValue)
        default: return nil
        }
    }
}
