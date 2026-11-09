import CoreGraphics

// MARK: - Card placement (the tutorial step card's one screen-edge helper)
//
// Pure geometry so the tests pin it: given the spotlight rect, the card's preferred
// size, and the usable screen, choose a frame for the card that NEVER intersects
// the spotlight. `above`/`below`/`beside`/`lower` are honoured when the card fits
// there; otherwise (and for `auto`) the largest clear region wins. When no region
// can hold the full card, the card goes compact: it keeps its width and shrinks to
// the height of the largest clear region.

/// Where a card would rather sit; `auto` takes the largest clear region.
enum SupportPlacement: String, CaseIterable {
    case auto, above, below, beside, lower, unknown
}

struct SupportCardPlacement: Equatable {
    enum Region: String, Equatable, CaseIterable { case above, below, leading, trailing }

    var frame: CGRect
    var region: Region
    /// The card had to shrink to fit (render the compact density).
    var isCompact: Bool

    /// Minimum height a compact card still makes sense at.
    static let minCompactHeight: CGFloat = 72

    /// - Parameters:
    ///   - spotlight: the target rect, already padded by the spotlight inset.
    ///   - card: the card's preferred size.
    ///   - bounds: the usable screen (safe area applied), same coordinate space.
    ///   - gap: space between spotlight and card.
    static func place(spotlight: CGRect, card: CGSize, in bounds: CGRect,
                      preference: SupportPlacement = .auto, gap: CGFloat = 12) -> SupportCardPlacement {
        let regions = clearRegions(spotlight: spotlight, bounds: bounds, gap: gap)
        let fits: (Region) -> Bool = { r in
            guard let rect = regions[r] else { return false }
            return rect.width >= card.width - 0.5 && rect.height >= card.height - 0.5
        }

        let preferred: [Region]
        switch preference {
        case .above: preferred = [.above]
        case .below: preferred = [.below]
        case .beside:
            let l = regions[.leading]?.width ?? 0, t = regions[.trailing]?.width ?? 0
            preferred = t >= l ? [.trailing, .leading] : [.leading, .trailing]
        case .lower:
            // The lower of the two vertical regions: prefer below, dock to the bottom.
            preferred = [.below]
        case .auto, .unknown: preferred = []
        }

        if let r = preferred.first(where: fits), let rect = regions[r] {
            return SupportCardPlacement(frame: position(card, in: rect, region: r, spotlight: spotlight,
                                                        dockBottom: preference == .lower),
                                        region: r, isCompact: false)
        }
        // Auto: the largest clear region the card fits, by area.
        let byArea = Region.allCases.compactMap { r in regions[r].map { (r, $0) } }
            .sorted { $0.1.width * $0.1.height > $1.1.width * $1.1.height }
        if let (r, rect) = byArea.first(where: { fits($0.0) }) {
            return SupportCardPlacement(frame: position(card, in: rect, region: r, spotlight: spotlight,
                                                        dockBottom: preference == .lower && r == .below),
                                        region: r, isCompact: false)
        }
        // Compact fallback: the vertical region with the most height (cards are wide),
        // else the largest region; the card shrinks to fit it.
        let vertical = [Region.above, .below].compactMap { r in regions[r].map { (r, $0) } }
            .max { $0.1.height < $1.1.height }
        let pick = (vertical.map { $0.1.height >= minCompactHeight } ?? false) ? vertical : byArea.first
        guard let (r, rect) = pick else {
            // No clear space at all (target covers the screen): dock at the bottom.
            let h = min(card.height, bounds.height)
            let f = CGRect(x: bounds.midX - min(card.width, bounds.width) / 2, y: bounds.maxY - h,
                           width: min(card.width, bounds.width), height: h)
            return SupportCardPlacement(frame: f, region: .below, isCompact: true)
        }
        let size = CGSize(width: min(card.width, rect.width), height: min(card.height, rect.height))
        return SupportCardPlacement(frame: position(size, in: rect, region: r, spotlight: spotlight, dockBottom: false),
                                    region: r, isCompact: true)
    }

    /// The four clear rectangles around the spotlight (clipped to `bounds`, minus `gap`).
    static func clearRegions(spotlight s: CGRect, bounds b: CGRect, gap: CGFloat) -> [Region: CGRect] {
        var out: [Region: CGRect] = [:]
        func add(_ r: Region, _ rect: CGRect) {
            if rect.width > 0, rect.height > 0 { out[r] = rect }
        }
        add(.above, CGRect(x: b.minX, y: b.minY, width: b.width, height: s.minY - gap - b.minY))
        add(.below, CGRect(x: b.minX, y: s.maxY + gap, width: b.width, height: b.maxY - (s.maxY + gap)))
        add(.leading, CGRect(x: b.minX, y: b.minY, width: s.minX - gap - b.minX, height: b.height))
        add(.trailing, CGRect(x: s.maxX + gap, y: b.minY, width: b.maxX - (s.maxX + gap), height: b.height))
        return out
    }

    /// Center the card on the spotlight along the free axis, clamped into `rect`.
    private static func position(_ card: CGSize, in rect: CGRect, region: Region,
                                 spotlight: CGRect, dockBottom: Bool) -> CGRect {
        func clamp(_ v: CGFloat, _ lo: CGFloat, _ hi: CGFloat) -> CGFloat { min(max(v, lo), max(lo, hi)) }
        let w = min(card.width, rect.width), h = min(card.height, rect.height)
        switch region {
        case .above:
            let x = clamp(spotlight.midX - w / 2, rect.minX, rect.maxX - w)
            return CGRect(x: x, y: rect.maxY - h, width: w, height: h)
        case .below:
            let x = clamp(spotlight.midX - w / 2, rect.minX, rect.maxX - w)
            return CGRect(x: x, y: dockBottom ? rect.maxY - h : rect.minY, width: w, height: h)
        case .leading:
            let y = clamp(spotlight.midY - h / 2, rect.minY, rect.maxY - h)
            return CGRect(x: rect.maxX - w, y: y, width: w, height: h)
        case .trailing:
            let y = clamp(spotlight.midY - h / 2, rect.minY, rect.maxY - h)
            return CGRect(x: rect.minX, y: y, width: w, height: h)
        }
    }
}

// MARK: - Banner docking (spec §6.1 `banner`)

enum SupportBannerDock: Equatable {
    case top, bottom

    /// The edge farthest from the target; bottom when there is no target.
    static func farthest(from target: CGRect?, in bounds: CGRect) -> SupportBannerDock {
        guard let t = target else { return .bottom }
        return (t.midY - bounds.minY) > (bounds.maxY - t.midY) ? .top : .bottom
    }
}
