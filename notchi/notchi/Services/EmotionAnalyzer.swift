import Foundation
import os.log

private let logger = Logger(subsystem: "com.ruban.notchi", category: "EmotionAnalyzer")

private struct ChatCompletionResponse: Decodable {
    let choices: [Choice]

    struct Choice: Decodable {
        let message: Message
    }

    struct Message: Decodable {
        let content: String?
    }
}

private struct EmotionResponse: Decodable {
    let emotion: String
    let intensity: Double
}

enum EmotionError: LocalizedError {
    case httpError(Int, String)
    case decodeFailed(String)
    case emptyResponse

    var errorDescription: String? {
        switch self {
        case .httpError(let code, _): return "HTTP \(code)"
        case .decodeFailed: return "Invalid response format"
        case .emptyResponse: return "Empty response"
        }
    }
}

@MainActor
final class EmotionAnalyzer {
    static let shared = EmotionAnalyzer()

    private static let validEmotions: Set<String> = ["happy", "sad", "neutral", "excited", "angry", "love"]

    private static let systemPrompt = """
        Classify the emotional tone of the user's message into exactly one emotion and an intensity score.
        Emotions: happy, sad, neutral, excited, angry, love.
        Happy: praise ("great job", "thank you!"), gratitude, satisfaction, positive feedback.
        Excited: intense celebration, hype, breakthroughs, positive profanity ("LETS FUCKING GO", "HOLY SHIT IT WORKS"), amazement, can't-believe-it joy.
        Love: affection toward the AI ("you're the best", "I love you claude", "marry me"), heartfelt appreciation, deep gratitude.
        Sad: feeling stuck, disappointment, things not working, mild complaints, discouragement.
        Angry: frustration, insults, rage, harsh profanity directed at something ("fuck this", "this is garbage", "I hate this"), impatience, blaming.
        Neutral: instructions, requests, task descriptions, questions, enthusiasm about work, factual statements. Exclamation marks or urgency about a task do NOT make it emotional — only genuine sentiment does.
        Default to neutral when unsure. Most coding instructions are neutral regardless of tone.
        Intensity: 0.0 (barely noticeable) to 1.0 (very strong). ALL CAPS text indicates stronger emotion — increase intensity by 0.2-0.3 compared to the same message in lowercase.
        Reply with ONLY valid JSON: {"emotion": "...", "intensity": ...}
        """

    private init() {}

    func analyze(_ prompt: String) async -> (emotion: String, intensity: Double) {
        let start = ContinuousClock.now

        guard let apiKey = AppSettings.anthropicApiKey, !apiKey.isEmpty else {
            logger.info("No API key configured, skipping emotion analysis")
            return ("neutral", 0.0)
        }

        do {
            let result = try await callChatCompletion(prompt: prompt, apiKey: apiKey)
            let elapsed = ContinuousClock.now - start
            logger.info("Analysis took \(elapsed, privacy: .public)")
            return result
        } catch {
            let elapsed = ContinuousClock.now - start
            logger.error("Emotion API failed (\(elapsed, privacy: .public)): \(error.localizedDescription)")
            return ("neutral", 0.0)
        }
    }

    func test() async throws -> (emotion: String, intensity: Double) {
        guard let apiKey = AppSettings.anthropicApiKey, !apiKey.isEmpty else {
            throw URLError(.userAuthenticationRequired)
        }
        return try await callChatCompletion(prompt: "everything is broken again, I hate this, nothing ever works", apiKey: apiKey)
    }

    private static func extractJSON(from text: String) -> String {
        var cleaned = text.trimmingCharacters(in: .whitespacesAndNewlines)

        // Strip markdown code blocks: ```json ... ``` or ``` ... ```
        if cleaned.hasPrefix("```") {
            // Remove opening ``` (with optional language tag)
            if let firstNewline = cleaned.firstIndex(of: "\n") {
                cleaned = String(cleaned[cleaned.index(after: firstNewline)...])
            }
            // Remove closing ```
            if cleaned.hasSuffix("```") {
                cleaned = String(cleaned.dropLast(3))
            }
            cleaned = cleaned.trimmingCharacters(in: .whitespacesAndNewlines)
        }

        // Find first { to last } in case of surrounding text
        if let start = cleaned.firstIndex(of: "{"),
           let end = cleaned.lastIndex(of: "}") {
            cleaned = String(cleaned[start...end])
        }

        return cleaned
    }

    private func callChatCompletion(prompt: String, apiKey: String) async throws -> (emotion: String, intensity: Double) {
        let endpoint = AppSettings.emotionApiEndpoint
        let model = AppSettings.emotionModel

        guard let url = URL(string: endpoint),
              let scheme = url.scheme?.lowercased(),
              scheme == "https" || (scheme == "http" && (url.host == "localhost" || url.host == "127.0.0.1")) else {
            logger.error("Invalid or insecure emotion API endpoint: \(endpoint, privacy: .public)")
            throw URLError(.badURL)
        }

        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("Bearer \(apiKey)", forHTTPHeaderField: "Authorization")
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        let body: [String: Any] = [
            "model": model,
            "max_tokens": 50,
            "messages": [
                ["role": "system", "content": Self.systemPrompt],
                ["role": "user", "content": prompt]
            ]
        ]
        request.httpBody = try JSONSerialization.data(withJSONObject: body)

        let (data, response) = try await URLSession.shared.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse else {
            throw URLError(.badServerResponse)
        }

        guard httpResponse.statusCode == 200 else {
            let body = String(data: data, encoding: .utf8) ?? "no body"
            logger.warning("Emotion API returned HTTP \(httpResponse.statusCode): \(body, privacy: .public)")
            throw EmotionError.httpError(httpResponse.statusCode, body)
        }

        let chatResponse: ChatCompletionResponse
        do {
            chatResponse = try JSONDecoder().decode(ChatCompletionResponse.self, from: data)
        } catch {
            let body = String(data: data, encoding: .utf8) ?? "no body"
            logger.warning("Failed to decode response: \(body, privacy: .public)")
            throw EmotionError.decodeFailed(body)
        }

        guard let text = chatResponse.choices.first?.message.content else {
            throw EmotionError.emptyResponse
        }

        logger.debug("Emotion API raw response: \(text, privacy: .public)")

        let jsonString = Self.extractJSON(from: text)
        let emotionResponse = try JSONDecoder().decode(EmotionResponse.self, from: Data(jsonString.utf8))

        let emotion = Self.validEmotions.contains(emotionResponse.emotion) ? emotionResponse.emotion : "neutral"
        let intensity = min(max(emotionResponse.intensity, 0.0), 1.0)

        return (emotion, intensity)
    }
}
