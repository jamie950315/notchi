import SwiftUI

struct EmotionParticlesView: View {
    let emotion: NotchiEmotion
    let size: CGFloat

    var body: some View {
        ZStack {
            switch emotion {
            case .excited:
                SparkleParticles(size: size)
            case .angry:
                SteamParticles(size: size)
            case .love:
                HeartParticles(size: size)
            case .happy:
                NoteParticles(size: size)
            case .sad:
                EmptyView()
            case .sob:
                EmptyView()
            case .neutral:
                EmptyView()
            }
        }
        .allowsHitTesting(false)
    }
}

// MARK: - Sparkles (excited)

private struct SparkleParticle: Identifiable {
    let id = UUID()
    var x: CGFloat
    var y: CGFloat
    var scale: CGFloat
    var rotation: Double
    var opacity: Double
}

private struct SparkleParticles: View {
    let size: CGFloat
    @State private var particles: [SparkleParticle] = []
    @State private var timer: Timer?

    var body: some View {
        ZStack {
            ForEach(particles) { p in
                Image(systemName: "sparkle")
                    .font(.system(size: 8 * p.scale))
                    .foregroundColor(Color(red: 1.0, green: 0.85, blue: 0.0))
                    .rotationEffect(.degrees(p.rotation))
                    .opacity(p.opacity)
                    .position(x: size / 2 + p.x, y: size / 2 + p.y)
            }
        }
        .frame(width: size, height: size)
        .onAppear { startEmitting() }
        .onDisappear { timer?.invalidate() }
    }

    private func startEmitting() {
        timer = Timer.scheduledTimer(withTimeInterval: 0.2, repeats: true) { _ in
            Task { @MainActor in
                let p = SparkleParticle(
                    x: CGFloat.random(in: -size * 0.5...size * 0.5),
                    y: CGFloat.random(in: -size * 0.6 ... -size * 0.1),
                    scale: CGFloat.random(in: 0.6...1.4),
                    rotation: Double.random(in: 0...360),
                    opacity: 1.0
                )
                particles.append(p)
                if let idx = particles.firstIndex(where: { $0.id == p.id }) {
                    withAnimation(.easeOut(duration: 0.8)) {
                        particles[idx].opacity = 0
                        particles[idx].y -= 15
                        particles[idx].rotation += 90
                    }
                }
                Task {
                    try? await Task.sleep(for: .milliseconds(900))
                    await MainActor.run {
                        particles.removeAll { $0.id == p.id }
                    }
                }
            }
        }
    }
}

// MARK: - Steam (angry)

private struct SteamPuff: Identifiable {
    let id = UUID()
    var x: CGFloat
    var y: CGFloat
    var scale: CGFloat
    var opacity: Double
}

private struct SteamParticles: View {
    let size: CGFloat
    @State private var puffs: [SteamPuff] = []
    @State private var timer: Timer?

    var body: some View {
        ZStack {
            ForEach(puffs) { p in
                Circle()
                    .fill(Color.red.opacity(0.3))
                    .frame(width: 6 * p.scale, height: 6 * p.scale)
                    .blur(radius: 2)
                    .opacity(p.opacity)
                    .position(x: size / 2 + p.x, y: size / 2 + p.y)
            }
        }
        .frame(width: size, height: size)
        .onAppear { startEmitting() }
        .onDisappear { timer?.invalidate() }
    }

    private func startEmitting() {
        timer = Timer.scheduledTimer(withTimeInterval: 0.15, repeats: true) { _ in
            Task { @MainActor in
                let side: CGFloat = Bool.random() ? -1 : 1
                let p = SteamPuff(
                    x: side * CGFloat.random(in: size * 0.15...size * 0.35),
                    y: -size * 0.3,
                    scale: CGFloat.random(in: 0.8...1.5),
                    opacity: 0.8
                )
                puffs.append(p)
                if let idx = puffs.firstIndex(where: { $0.id == p.id }) {
                    withAnimation(.easeOut(duration: 0.6)) {
                        puffs[idx].opacity = 0
                        puffs[idx].y -= 12
                        puffs[idx].scale *= 1.8
                    }
                }
                Task {
                    try? await Task.sleep(for: .milliseconds(700))
                    await MainActor.run {
                        puffs.removeAll { $0.id == p.id }
                    }
                }
            }
        }
    }
}

// MARK: - Hearts (love)

private struct HeartParticle: Identifiable {
    let id = UUID()
    var x: CGFloat
    var y: CGFloat
    var scale: CGFloat
    var opacity: Double
}

private struct HeartParticles: View {
    let size: CGFloat
    @State private var hearts: [HeartParticle] = []
    @State private var timer: Timer?

    var body: some View {
        ZStack {
            ForEach(hearts) { h in
                Image(systemName: "heart.fill")
                    .font(.system(size: 7 * h.scale))
                    .foregroundColor(Color(red: 1.0, green: 0.35, blue: 0.55))
                    .opacity(h.opacity)
                    .position(x: size / 2 + h.x, y: size / 2 + h.y)
            }
        }
        .frame(width: size, height: size)
        .onAppear { startEmitting() }
        .onDisappear { timer?.invalidate() }
    }

    private func startEmitting() {
        timer = Timer.scheduledTimer(withTimeInterval: 0.5, repeats: true) { _ in
            Task { @MainActor in
                let h = HeartParticle(
                    x: CGFloat.random(in: -size * 0.3...size * 0.3),
                    y: -size * 0.15,
                    scale: CGFloat.random(in: 0.7...1.3),
                    opacity: 1.0
                )
                hearts.append(h)
                if let idx = hearts.firstIndex(where: { $0.id == h.id }) {
                    withAnimation(.easeOut(duration: 1.5)) {
                        hearts[idx].opacity = 0
                        hearts[idx].y -= 30
                        hearts[idx].x += CGFloat.random(in: -8...8)
                    }
                }
                Task {
                    try? await Task.sleep(for: .milliseconds(1600))
                    await MainActor.run {
                        hearts.removeAll { $0.id == h.id }
                    }
                }
            }
        }
    }
}

// MARK: - Notes (happy)

private struct NoteParticle: Identifiable {
    let id = UUID()
    let symbol: String
    var x: CGFloat
    var y: CGFloat
    var opacity: Double
}

private struct NoteParticles: View {
    let size: CGFloat
    private static let symbols = ["♪", "♫", "♬"]
    @State private var notes: [NoteParticle] = []
    @State private var timer: Timer?

    var body: some View {
        ZStack {
            ForEach(notes) { n in
                Text(n.symbol)
                    .font(.system(size: 10))
                    .foregroundColor(Color(red: 0.3, green: 0.9, blue: 0.4))
                    .opacity(n.opacity)
                    .position(x: size / 2 + n.x, y: size / 2 + n.y)
            }
        }
        .frame(width: size, height: size)
        .onAppear { startEmitting() }
        .onDisappear { timer?.invalidate() }
    }

    private func startEmitting() {
        timer = Timer.scheduledTimer(withTimeInterval: 0.7, repeats: true) { _ in
            Task { @MainActor in
                let n = NoteParticle(
                    symbol: Self.symbols.randomElement()!,
                    x: CGFloat.random(in: -size * 0.25...size * 0.35),
                    y: -size * 0.2,
                    opacity: 0.9
                )
                notes.append(n)
                if let idx = notes.firstIndex(where: { $0.id == n.id }) {
                    withAnimation(.easeOut(duration: 1.2)) {
                        notes[idx].opacity = 0
                        notes[idx].y -= 25
                        notes[idx].x += CGFloat.random(in: -10...10)
                    }
                }
                Task {
                    try? await Task.sleep(for: .milliseconds(1300))
                    await MainActor.run {
                        notes.removeAll { $0.id == n.id }
                    }
                }
            }
        }
    }
}

// MARK: - Tears (sad / sob)

private enum TearIntensity {
    case light, heavy

    var interval: TimeInterval {
        switch self {
        case .light: return 0.6
        case .heavy: return 0.2
        }
    }

    var count: Int {
        switch self {
        case .light: return 1
        case .heavy: return 2
        }
    }
}

private struct TearDrop: Identifiable {
    let id = UUID()
    var x: CGFloat
    var y: CGFloat
    var opacity: Double
}

private struct TearDrops: View {
    let size: CGFloat
    let intensity: TearIntensity
    @State private var tears: [TearDrop] = []
    @State private var timer: Timer?

    var body: some View {
        ZStack {
            ForEach(tears) { t in
                Capsule()
                    .fill(Color(red: 0.4, green: 0.6, blue: 1.0))
                    .frame(width: 2, height: 5)
                    .opacity(t.opacity)
                    .position(x: size / 2 + t.x, y: size / 2 + t.y)
            }
        }
        .frame(width: size, height: size)
        .onAppear { startEmitting() }
        .onDisappear { timer?.invalidate() }
    }

    private func startEmitting() {
        timer = Timer.scheduledTimer(withTimeInterval: intensity.interval, repeats: true) { _ in
            Task { @MainActor in
                for _ in 0..<intensity.count {
                    let t = TearDrop(
                        x: CGFloat.random(in: -size * 0.15...size * 0.15),
                        y: -size * 0.05,
                        opacity: 0.8
                    )
                    tears.append(t)
                    if let idx = tears.firstIndex(where: { $0.id == t.id }) {
                        withAnimation(.easeIn(duration: 0.5)) {
                            tears[idx].y += 25
                            tears[idx].opacity = 0
                        }
                    }
                    Task {
                        try? await Task.sleep(for: .milliseconds(600))
                        await MainActor.run {
                            tears.removeAll { $0.id == t.id }
                        }
                    }
                }
            }
        }
    }
}
