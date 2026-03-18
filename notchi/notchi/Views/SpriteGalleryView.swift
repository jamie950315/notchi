import SwiftUI

struct SpriteGalleryView: View {
    private let tasks: [NotchiTask] = [.idle, .working, .waiting, .sleeping, .compacting]
    private let emotions: [NotchiEmotion] = NotchiEmotion.allCases

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 16) {
                ForEach(emotions, id: \.rawValue) { emotion in
                    VStack(alignment: .leading, spacing: 6) {
                        Text(emotion.rawValue.capitalized)
                            .font(.system(size: 11, weight: .semibold, design: .monospaced))
                            .foregroundColor(labelColor(for: emotion))

                        HStack(spacing: 8) {
                            ForEach(tasks, id: \.rawValue) { task in
                                let state = NotchiState(task: task, emotion: emotion)
                                VStack(spacing: 2) {
                                    ZStack {
                                        SpriteSheetView(
                                            spriteSheet: state.spriteSheetName,
                                            frameCount: state.frameCount,
                                            columns: state.columns,
                                            fps: state.animationFPS,
                                            isAnimating: true
                                        )
                                        .frame(width: 48, height: 48)

                                        EmotionParticlesView(emotion: emotion, size: 48)
                                    }
                                    .frame(width: 56, height: 56)

                                    Text(task.rawValue)
                                        .font(.system(size: 8, design: .monospaced))
                                        .foregroundColor(TerminalColors.dimmedText)
                                }
                            }
                        }
                    }
                    .padding(.horizontal, 4)
                }
            }
            .padding(.top, 8)
        }
        .scrollIndicators(.hidden)
    }

    private func labelColor(for emotion: NotchiEmotion) -> Color {
        switch emotion {
        case .neutral:  return TerminalColors.secondaryText
        case .happy:    return Color(red: 0.3, green: 0.9, blue: 0.4)
        case .sad:      return Color(red: 0.4, green: 0.5, blue: 0.9)
        case .sob:      return Color(red: 0.3, green: 0.4, blue: 0.8)
        case .excited:  return Color(red: 1.0, green: 0.85, blue: 0.0)
        case .angry:    return Color(red: 1.0, green: 0.3, blue: 0.2)
        case .love:     return Color(red: 1.0, green: 0.4, blue: 0.6)
        }
    }
}
