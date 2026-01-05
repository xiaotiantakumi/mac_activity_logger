import SwiftUI

struct DashboardView: View {
    @Environment(ActivityController.self) var controller
    
    var body: some View {
        VStack(spacing: 20) {
            // Status Card
            VStack {
                Text("Status")
                    .font(.headline)
                    .foregroundStyle(.secondary)
                
                HStack {
                    Circle()
                        .fill(controller.isMonitoring ? Color.green : Color.red)
                        .frame(width: 12, height: 12)
                    Text(controller.statusMessage)
                        .font(.title2)
                        .bold()
                }
            }
            .padding()
            .frame(maxWidth: .infinity)
            .background(Color(nsColor: .controlBackgroundColor))
            .cornerRadius(12)
            
            // Action Button
            Button(action: {
                if controller.isMonitoring {
                    controller.stopMonitoring()
                } else {
                    controller.startMonitoring()
                }
            }) {
                HStack {
                    Image(systemName: controller.isMonitoring ? "stop.fill" : "play.fill")
                    Text(controller.isMonitoring ? "Stop Monitoring" : "Start Monitoring")
                }
                .font(.title3)
                .padding()
                .frame(maxWidth: .infinity)
            }
            .buttonStyle(.borderedProminent)
            .tint(controller.isMonitoring ? .red : .green)
            .controlSize(.large)
            
            // Recent Activity
            VStack(alignment: .leading) {
                Text("Recent Activity")
                    .font(.headline)
                    .padding(.bottom, 5)
                
                List {
                    if controller.recentLogs.isEmpty {
                        Text("No activity recorded yet.")
                            .foregroundStyle(.secondary)
                    } else {
                        ForEach(controller.recentLogs, id: \.self) { log in
                            Text(log)
                        }
                    }
                }
                .listStyle(.plain)
                .background(Color(nsColor: .controlBackgroundColor))
                .cornerRadius(12)
            }
        }
        .padding()
    }
}
