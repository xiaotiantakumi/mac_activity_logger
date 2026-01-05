import SwiftUI

@main
struct ActivityLoggerApp: App {
    @NSApplicationDelegateAdaptor(AppDelegate.self) var appDelegate
    @State private var controller = ActivityController()

    var body: some Scene {
        WindowGroup {
            ContentView()
                .environment(controller)
                .onAppear {
                    print("DEBUG: ContentView appeared")
                }
        }
        .commands {
            SidebarCommands() // Enable sidebar toggle
        }
    }
}

class AppDelegate: NSObject, NSApplicationDelegate {
    func applicationDidFinishLaunching(_ notification: Notification) {
        // Force the app to be a foreground app
        NSApp.setActivationPolicy(.regular)
        NSApp.activate(ignoringOtherApps: true)
        print("DEBUG: Application finished launching and activated")
    }
}
