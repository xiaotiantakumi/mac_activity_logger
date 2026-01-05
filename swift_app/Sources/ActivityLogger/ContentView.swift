import SwiftUI

struct ContentView: View {
    @State private var selectedView: String? = "dashboard"

    var body: some View {
        NavigationSplitView {
            List(selection: $selectedView) {
                Label("Dashboard", systemImage: "square.grid.2x2")
                    .tag("dashboard")
                Label("History", systemImage: "clock")
                    .tag("history")
                Label("Settings", systemImage: "gear")
                    .tag("settings")
            }
            .navigationSplitViewColumnWidth(min: 200, ideal: 250)
            .listStyle(.sidebar)
        } detail: {
            switch selectedView {
            case "dashboard":
                DashboardView()
            case "history":
                HistoryView()
            case "settings":
                SettingsView()
            default:
                Text("Select an item")
            }
        }
        .frame(minWidth: 800, minHeight: 600)
    }
}
