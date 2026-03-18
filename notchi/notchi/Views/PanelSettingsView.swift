import ServiceManagement
import SwiftUI

struct PanelSettingsView: View {
    @State private var launchAtLogin = SMAppService.mainApp.status == .enabled
    @State private var hooksInstalled = HookInstaller.isInstalled()
    @State private var hooksError = false
    @State private var apiKeyInput = AppSettings.anthropicApiKey ?? ""
    @State private var endpointInput = AppSettings.emotionApiEndpoint
    @State private var modelInput = AppSettings.emotionModel
    @State private var testState: EmotionTestState = .idle
    @State private var showingSpriteGallery = false
    @ObservedObject private var updateManager = UpdateManager.shared
    private var usageConnected: Bool { ClaudeUsageService.shared.isConnected }
    private var hasApiKey: Bool { !apiKeyInput.isEmpty }

    private var hookStatusText: String {
        if hooksError { return "Error" }
        if hooksInstalled { return "Installed" }
        return "Not Installed"
    }

    private var hookStatusColor: Color {
        hooksInstalled && !hooksError ? TerminalColors.green : TerminalColors.red
    }

    var body: some View {
        if showingSpriteGallery {
            VStack(alignment: .leading, spacing: 0) {
                Button(action: { showingSpriteGallery = false }) {
                    HStack(spacing: 5) {
                        Image(systemName: "chevron.left")
                            .font(.system(size: 11, weight: .semibold))
                        Text("Settings")
                            .font(.system(size: 12, weight: .medium))
                    }
                    .foregroundColor(.white.opacity(0.7))
                }
                .buttonStyle(.plain)
                .padding(.horizontal, 12)
                .padding(.top, 10)

                SpriteGalleryView()
            }
            .frame(maxWidth: .infinity, maxHeight: .infinity)
        } else {
            settingsContent
        }
    }

    private var settingsContent: some View {
        VStack(alignment: .leading, spacing: 0) {
            ScrollView {
                VStack(alignment: .leading, spacing: 16) {
                    displaySection
                    Divider().background(Color.white.opacity(0.08))
                    togglesSection
                    Divider().background(Color.white.opacity(0.08))
                    actionsSection
                }
                .padding(.top, 10)
            }
            .scrollIndicators(.hidden)

            Spacer()

            quitSection
        }
        .padding(.horizontal, 12)
        .padding(.top, 10)
        .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .topLeading)
    }

    private var displaySection: some View {
        VStack(alignment: .leading, spacing: 12) {
            ScreenPickerRow(screenSelector: ScreenSelector.shared)

            SoundPickerView()
        }
    }

    private var togglesSection: some View {
        VStack(alignment: .leading, spacing: 12) {
            Button(action: toggleLaunchAtLogin) {
                SettingsRowView(icon: "power", title: "Launch at Login") {
                    ToggleSwitch(isOn: launchAtLogin)
                }
            }
            .buttonStyle(.plain)

            Button(action: installHooksIfNeeded) {
                SettingsRowView(icon: "terminal", title: "Hooks") {
                    statusBadge(hookStatusText, color: hookStatusColor)
                }
            }
            .buttonStyle(.plain)

            Button(action: connectUsage) {
                SettingsRowView(icon: "gauge.with.dots.needle.33percent", title: "Claude Usage") {
                    statusBadge(
                        usageConnected ? "Connected" : "Not Connected",
                        color: usageConnected ? TerminalColors.green : TerminalColors.red
                    )
                }
            }
            .buttonStyle(.plain)

            apiKeyRow
        }
    }

    private var apiKeyRow: some View {
        VStack(alignment: .leading, spacing: 6) {
            SettingsRowView(icon: "brain", title: "Emotion Analysis") {
                statusBadge(
                    hasApiKey ? "Active" : "No Key",
                    color: hasApiKey ? TerminalColors.green : TerminalColors.red
                )
            }

            VStack(spacing: 6) {
                settingsTextField(text: $endpointInput, placeholder: "API Endpoint")

                HStack(spacing: 6) {
                    settingsTextField(text: $modelInput, placeholder: "Model")

                    SecureField("", text: $apiKeyInput)
                        .textFieldStyle(.plain)
                        .font(.system(size: 11, design: .monospaced))
                        .foregroundColor(TerminalColors.primaryText)
                        .padding(.horizontal, 8)
                        .padding(.vertical, 5)
                        .background(Color.white.opacity(0.06))
                        .cornerRadius(6)
                        .overlay(alignment: .leading) {
                            if apiKeyInput.isEmpty {
                                Text("API Key")
                                    .font(.system(size: 11, design: .monospaced))
                                    .foregroundColor(TerminalColors.dimmedText)
                                    .padding(.leading, 8)
                                    .allowsHitTesting(false)
                            }
                        }
                }
                Button(action: testEmotionApi) {
                    HStack(spacing: 4) {
                        switch testState {
                        case .idle:
                            Image(systemName: "play.circle")
                                .font(.system(size: 11))
                            Text("Test")
                                .font(.system(size: 11, weight: .medium))
                        case .testing:
                            ProgressView()
                                .controlSize(.mini)
                            Text("Testing...")
                                .font(.system(size: 11, weight: .medium))
                        case .success:
                            Image(systemName: "checkmark.circle.fill")
                                .font(.system(size: 11))
                            Text("Connected")
                                .font(.system(size: 11, weight: .medium))
                        case .failure(let message):
                            Image(systemName: "xmark.circle.fill")
                                .font(.system(size: 11))
                            Text(message)
                                .font(.system(size: 11, weight: .medium))
                                .lineLimit(1)
                        }
                    }
                    .foregroundColor(testState.color)
                    .padding(.horizontal, 8)
                    .padding(.vertical, 4)
                    .background(testState.color.opacity(0.12))
                    .cornerRadius(6)
                }
                .buttonStyle(.plain)
                .disabled(testState == .testing || !hasApiKey)
            }
            .padding(.leading, 28)
            .onChange(of: endpointInput) { saveEmotionSettings() }
            .onChange(of: modelInput) { saveEmotionSettings() }
            .onChange(of: apiKeyInput) { saveEmotionSettings() }
        }
    }

    private func testEmotionApi() {
        testState = .testing
        Task {
            do {
                _ = try await EmotionAnalyzer.shared.test()
                testState = .success("")
            } catch let error as URLError where error.code == .userAuthenticationRequired {
                testState = .failure("No API key")
            } catch {
                testState = .failure(error.localizedDescription)
            }
            try? await Task.sleep(for: .seconds(4))
            testState = .idle
        }
    }

    private func settingsTextField(text: Binding<String>, placeholder: String) -> some View {
        TextField("", text: text)
            .textFieldStyle(.plain)
            .font(.system(size: 11, design: .monospaced))
            .foregroundColor(TerminalColors.primaryText)
            .padding(.horizontal, 8)
            .padding(.vertical, 5)
            .background(Color.white.opacity(0.06))
            .cornerRadius(6)
            .overlay(alignment: .leading) {
                if text.wrappedValue.isEmpty {
                    Text(placeholder)
                        .font(.system(size: 11, design: .monospaced))
                        .foregroundColor(TerminalColors.dimmedText)
                        .padding(.leading, 8)
                        .allowsHitTesting(false)
                }
            }
    }

    private func saveEmotionSettings() {
        let trimmedKey = apiKeyInput.trimmingCharacters(in: .whitespacesAndNewlines)
        AppSettings.anthropicApiKey = trimmedKey.isEmpty ? nil : trimmedKey

        let trimmedEndpoint = endpointInput.trimmingCharacters(in: .whitespacesAndNewlines)
        if !trimmedEndpoint.isEmpty {
            AppSettings.emotionApiEndpoint = trimmedEndpoint
        }

        let trimmedModel = modelInput.trimmingCharacters(in: .whitespacesAndNewlines)
        if !trimmedModel.isEmpty {
            AppSettings.emotionModel = trimmedModel
        }
    }

    private var actionsSection: some View {
        VStack(alignment: .leading, spacing: 12) {
            Button(action: { showingSpriteGallery = true }) {
                SettingsRowView(icon: "person.3.sequence", title: "Sprite Gallery") {
                    Image(systemName: "chevron.right")
                        .font(.system(size: 10))
                        .foregroundColor(TerminalColors.dimmedText)
                }
            }
            .buttonStyle(.plain)

            Button(action: { updateManager.checkForUpdates() }) {
                SettingsRowView(icon: "arrow.triangle.2.circlepath", title: "Check for Updates") {
                    updateStatusView
                }
            }
            .buttonStyle(.plain)

            Button(action: openGitHubRepo) {
                SettingsRowView(icon: "star", title: "Star on GitHub") {
                    Image(systemName: "arrow.up.right")
                        .font(.system(size: 10))
                        .foregroundColor(TerminalColors.dimmedText)
                }
            }
            .buttonStyle(.plain)
        }
    }

    private func openGitHubRepo() {
        NSWorkspace.shared.open(URL(string: "https://github.com/sk-ruban/notchi")!)
    }

    private var quitSection: some View {
        Button(action: {
            NSApplication.shared.terminate(nil)
        }) {
            HStack {
                Image(systemName: "xmark.circle")
                    .font(.system(size: 13))
                Text("Quit Notchi")
                    .font(.system(size: 12, weight: .medium))
            }
            .foregroundColor(TerminalColors.red)
            .frame(maxWidth: .infinity, alignment: .leading)
            .padding(.vertical, 10)
            .padding(.horizontal, 12)
            .background(TerminalColors.red.opacity(0.1))
            .contentShape(Rectangle())
            .cornerRadius(8)
        }
        .buttonStyle(.plain)
        .padding(.bottom, 8)
    }

    private func toggleLaunchAtLogin() {
        do {
            if launchAtLogin {
                try SMAppService.mainApp.unregister()
            } else {
                try SMAppService.mainApp.register()
            }
            launchAtLogin = SMAppService.mainApp.status == .enabled
        } catch {
            print("Failed to toggle launch at login: \(error)")
        }
    }

    private func connectUsage() {
        ClaudeUsageService.shared.connectAndStartPolling()
    }

    private func installHooksIfNeeded() {
        guard !hooksInstalled else { return }
        hooksError = false
        let success = HookInstaller.installIfNeeded()
        if success {
            hooksInstalled = HookInstaller.isInstalled()
        } else {
            hooksError = true
        }
    }

    private func statusBadge(_ text: String, color: Color) -> some View {
        Text(text)
            .font(.system(size: 10, weight: .medium))
            .foregroundColor(color)
            .padding(.horizontal, 6)
            .padding(.vertical, 2)
            .background(color.opacity(0.15))
            .cornerRadius(4)
    }

    @ViewBuilder
    private var updateStatusView: some View {
        switch updateManager.state {
        case .checking:
            HStack(spacing: 4) {
                ProgressView()
                    .controlSize(.mini)
                Text("Checking...")
                    .font(.system(size: 10))
                    .foregroundColor(TerminalColors.dimmedText)
            }
        case .upToDate:
            statusBadge("Up to date", color: TerminalColors.green)
        case .found(let version, _):
            statusBadge("v\(version) available", color: TerminalColors.amber)
        case .downloading(let progress):
            HStack(spacing: 4) {
                ProgressView(value: progress)
                    .frame(width: 40)
                Text("\(Int(progress * 100))%")
                    .font(.system(size: 10))
                    .foregroundColor(TerminalColors.dimmedText)
            }
        case .extracting:
            HStack(spacing: 4) {
                ProgressView()
                    .controlSize(.mini)
                Text("Installing...")
                    .font(.system(size: 10))
                    .foregroundColor(TerminalColors.dimmedText)
            }
        case .readyToInstall(let version):
            Button(action: { updateManager.downloadAndInstall() }) {
                statusBadge("Install v\(version)", color: TerminalColors.green)
            }
            .buttonStyle(.plain)
        case .installing:
            HStack(spacing: 4) {
                ProgressView()
                    .controlSize(.mini)
                Text("Installing...")
                    .font(.system(size: 10))
                    .foregroundColor(TerminalColors.dimmedText)
            }
        case .error(let message):
            statusBadge(message, color: TerminalColors.red)
        case .idle:
            Text("v\(Bundle.main.object(forInfoDictionaryKey: "CFBundleShortVersionString") as? String ?? "1.0")")
                .font(.system(size: 10))
                .foregroundColor(TerminalColors.dimmedText)
        }
    }
}

struct SettingsRowView<Trailing: View>: View {
    let icon: String
    let title: String
    @ViewBuilder let trailing: () -> Trailing

    var body: some View {
        HStack {
            Image(systemName: icon)
                .font(.system(size: 12))
                .foregroundColor(TerminalColors.secondaryText)
                .frame(width: 20)

            Text(title)
                .font(.system(size: 12))
                .foregroundColor(TerminalColors.primaryText)

            Spacer()

            trailing()
        }
        .padding(.vertical, 4)
        .contentShape(Rectangle())
    }
}

struct ToggleSwitch: View {
    let isOn: Bool

    var body: some View {
        ZStack(alignment: isOn ? .trailing : .leading) {
            Capsule()
                .fill(isOn ? TerminalColors.green : Color.white.opacity(0.15))
                .frame(width: 32, height: 18)

            Circle()
                .fill(Color.white)
                .frame(width: 14, height: 14)
                .padding(2)
        }
        .animation(.easeInOut(duration: 0.15), value: isOn)
    }
}

private enum EmotionTestState: Equatable {
    case idle
    case testing
    case success(String)
    case failure(String)

    var color: Color {
        switch self {
        case .idle: return TerminalColors.dimmedText
        case .testing: return TerminalColors.dimmedText
        case .success: return TerminalColors.green
        case .failure: return TerminalColors.red
        }
    }
}

#Preview {
    PanelSettingsView()
        .frame(width: 402, height: 400)
        .background(Color.black)
}
