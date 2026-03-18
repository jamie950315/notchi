import AppKit

enum NotchiTask: String, CaseIterable {
    case idle, working, sleeping, compacting, waiting

    var animationFPS: Double {
        switch self {
        case .compacting: return 6.0
        case .sleeping: return 2.0
        case .idle, .waiting: return 3.0
        case .working: return 4.0
        }
    }

    var spritePrefix: String { rawValue }

    var bobDuration: Double {
        switch self {
        case .sleeping:   return 4.0
        case .idle, .waiting: return 1.5
        case .working:    return 0.4
        case .compacting: return 0.5
        }
    }

    var bobAmplitude: CGFloat {
        switch self {
        case .sleeping, .compacting: return 0
        case .idle:                  return 1.5
        case .waiting:               return 0.5
        case .working:               return 0.5
        }
    }

    var canWalk: Bool {
        switch self {
        case .sleeping, .compacting, .waiting:
            return false
        case .idle, .working:
            return true
        }
    }

    var displayName: String {
        switch self {
        case .idle:       return "Idle"
        case .working:    return "Working..."
        case .sleeping:   return "Sleeping"
        case .compacting: return "Compacting..."
        case .waiting:    return "Waiting..."
        }
    }

    var walkFrequencyRange: ClosedRange<Double> {
        switch self {
        case .sleeping, .waiting: return 30.0...60.0
        case .idle:               return 8.0...15.0
        case .working:            return 5.0...12.0
        case .compacting:         return 15.0...25.0
        }
    }

    var frameCount: Int {
        switch self {
        case .compacting: return 5
        default: return 6
        }
    }

    var columns: Int {
        switch self {
        case .compacting: return 5
        default: return 6
        }
    }
}

enum NotchiEmotion: String, CaseIterable {
    case neutral, happy, sad, sob, excited, angry, love

    var swayAmplitude: Double {
        switch self {
        case .neutral:  return 0.4
        case .happy:    return 0.8
        case .sad:      return 0.2
        case .sob:      return 0.1
        case .excited:  return 1.2
        case .angry:    return 0.2
        case .love:     return 0.6
        }
    }

    /// Sprite sheet fallback: excited/love → happy, angry → sad, sob → sad
    var spriteFallback: NotchiEmotion? {
        switch self {
        case .excited, .love: return .happy
        case .angry:          return .sad
        case .sob:            return .sad
        default:              return nil
        }
    }

    var bobMultiplier: CGFloat {
        switch self {
        case .excited:  return 1.5
        case .happy:    return 1.1
        case .love:     return 1.0
        case .neutral:  return 1.0
        case .angry:    return 0.6
        case .sad:      return 0.4
        case .sob:      return 0
        }
    }

    var fpsMultiplier: Double {
        switch self {
        case .excited:  return 1.4
        case .angry:    return 1.2
        case .happy:    return 1.1
        case .love:     return 0.85
        case .neutral:  return 1.0
        case .sad:      return 0.7
        case .sob:      return 0.5
        }
    }

    var bobDurationMultiplier: Double {
        switch self {
        case .excited:  return 0.6
        case .angry:    return 0.8
        case .happy:    return 0.85
        case .love:     return 1.3
        case .neutral:  return 1.0
        case .sad:      return 1.5
        case .sob:      return 1.0
        }
    }

    var trembleAmplitude: CGFloat {
        switch self {
        case .sob:      return 0.25
        case .angry:    return 0.35
        case .excited:  return 0.08
        default:        return 0
        }
    }

    var scalePulse: CGFloat {
        switch self {
        case .excited:  return 0.04
        case .angry:    return 0.02
        case .love:     return 0.03
        case .happy:    return 0.015
        default:        return 0
        }
    }

    var canWalk: Bool {
        switch self {
        case .sob, .angry: return false
        default:           return true
        }
    }
}

struct NotchiState: Equatable {
    var task: NotchiTask
    var emotion: NotchiEmotion = .neutral

    /// Resolves the sprite sheet name with fallback chain.
    var spriteSheetName: String {
        let name = "\(task.spritePrefix)_\(emotion.rawValue)"
        if NSImage(named: name) != nil { return name }
        if let fallback = emotion.spriteFallback {
            let fallbackName = "\(task.spritePrefix)_\(fallback.rawValue)"
            if NSImage(named: fallbackName) != nil { return fallbackName }
        }
        return "\(task.spritePrefix)_neutral"
    }
    var animationFPS: Double { task.animationFPS * emotion.fpsMultiplier }
    var bobDuration: Double { task.bobDuration * emotion.bobDurationMultiplier }
    var bobAmplitude: CGFloat { task.bobAmplitude * emotion.bobMultiplier }
    var swayAmplitude: Double { emotion.swayAmplitude }
    var trembleAmplitude: CGFloat { emotion.trembleAmplitude }
    var scalePulse: CGFloat { emotion.scalePulse }
    var canWalk: Bool { emotion.canWalk && task.canWalk }
    var displayName: String { task.displayName }
    var walkFrequencyRange: ClosedRange<Double> { task.walkFrequencyRange }
    var frameCount: Int { task.frameCount }
    var columns: Int { task.columns }

    static let idle = NotchiState(task: .idle)
    static let working = NotchiState(task: .working)
    static let sleeping = NotchiState(task: .sleeping)
    static let compacting = NotchiState(task: .compacting)
    static let waiting = NotchiState(task: .waiting)
}
