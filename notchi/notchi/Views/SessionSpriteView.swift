import SwiftUI

struct SessionSpriteView: View {
    let state: NotchiState
    let isSelected: Bool

    private var bobAmplitude: CGFloat {
        guard state.bobAmplitude > 0 else { return 0 }
        return isSelected ? state.bobAmplitude : state.bobAmplitude * 0.67
    }

    private var isAnimating: Bool {
        bobAmplitude > 0 || state.trembleAmplitude > 0 || state.scalePulse > 0
    }

    private func scalePulseValue(at date: Date) -> CGFloat {
        guard state.scalePulse > 0 else { return 1.0 }
        let t = date.timeIntervalSinceReferenceDate
        let speed: Double = state.emotion == .excited ? 3.0 : 1.5
        let phase = (t * speed).truncatingRemainder(dividingBy: 1.0)
        return 1.0 + CGFloat(sin(phase * .pi * 2)) * state.scalePulse
    }

    var body: some View {
        TimelineView(.animation(minimumInterval: 1.0 / 30, paused: !isAnimating)) { timeline in
            SpriteSheetView(
                spriteSheet: state.spriteSheetName,
                frameCount: state.frameCount,
                columns: state.columns,
                fps: state.animationFPS,
                isAnimating: true
            )
            .frame(width: 32, height: 32)
            .overlay {
                EmotionParticlesView(emotion: state.emotion, size: 32)
            }
            .scaleEffect(scalePulseValue(at: timeline.date))
            .offset(
                x: trembleOffset(at: timeline.date, amplitude: state.trembleAmplitude),
                y: bobOffset(at: timeline.date, duration: state.bobDuration, amplitude: bobAmplitude)
            )
        }
    }
}
