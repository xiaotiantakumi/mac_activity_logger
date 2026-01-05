import SwiftUI

struct SettingsView: View {
    @AppStorage("interval") private var interval: Double = 2.0
    @AppStorage("enableAudio") private var enableAudio: Bool = true
    @AppStorage("enableSummarization") private var enableSummarization: Bool = true
    
    var body: some View {
        Form {
            Section("Capture Settings") {
                HStack {
                    Text("Capture Interval")
                    Slider(value: $interval, in: 1.0...60.0, step: 1.0)
                    Text("\(Int(interval))s")
                        .monospacedDigit()
                }
            }
            
            Section("Features") {
                Toggle("Enable Audio Recording", isOn: $enableAudio)
                Toggle("Enable AI Summarization", isOn: $enableSummarization)
            }
            
            Section("Storage") {
                LabeledContent("Logs Directory", value: "~/Documents/mac_logs")
                Button("Open Logs Folder") {
                    // TODO: Implement open folder
                }
            }
        }
        .formStyle(.grouped)
        .padding()
    }
}
