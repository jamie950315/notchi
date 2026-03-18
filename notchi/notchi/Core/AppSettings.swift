import Foundation

struct AppSettings {
    private static let notificationSoundKey = "notificationSound"
    private static let isMutedKey = "isMuted"
    private static let previousSoundKey = "previousNotificationSound"
    private static let isUsageEnabledKey = "isUsageEnabled"
    private static let emotionApiEndpointKey = "emotionApiEndpoint"
    private static let emotionModelKey = "emotionModel"

    static var isUsageEnabled: Bool {
        get { UserDefaults.standard.bool(forKey: isUsageEnabledKey) }
        set { UserDefaults.standard.set(newValue, forKey: isUsageEnabledKey) }
    }

    static var anthropicApiKey: String? {
        get { KeychainManager.getAnthropicApiKey() }
        set { KeychainManager.setAnthropicApiKey(newValue) }
    }

    static var emotionApiEndpoint: String {
        get { UserDefaults.standard.string(forKey: emotionApiEndpointKey) ?? "https://api.openai.com/v1/chat/completions" }
        set { UserDefaults.standard.set(newValue, forKey: emotionApiEndpointKey) }
    }

    static var emotionModel: String {
        get { UserDefaults.standard.string(forKey: emotionModelKey) ?? "gpt-4o-mini" }
        set { UserDefaults.standard.set(newValue, forKey: emotionModelKey) }
    }

    static var notificationSound: NotificationSound {
        get {
            guard let rawValue = UserDefaults.standard.string(forKey: notificationSoundKey),
                  let sound = NotificationSound(rawValue: rawValue) else {
                return .purr
            }
            return sound
        }
        set {
            UserDefaults.standard.set(newValue.rawValue, forKey: notificationSoundKey)
        }
    }

    static var isMuted: Bool {
        get { UserDefaults.standard.bool(forKey: isMutedKey) }
        set { UserDefaults.standard.set(newValue, forKey: isMutedKey) }
    }

    static func toggleMute() {
        if isMuted {
            notificationSound = previousSound ?? .purr
            isMuted = false
        } else {
            previousSound = notificationSound
            notificationSound = .none
            isMuted = true
        }
    }

    private static var previousSound: NotificationSound? {
        get {
            guard let rawValue = UserDefaults.standard.string(forKey: previousSoundKey) else {
                return nil
            }
            return NotificationSound(rawValue: rawValue)
        }
        set {
            UserDefaults.standard.set(newValue?.rawValue, forKey: previousSoundKey)
        }
    }
}
