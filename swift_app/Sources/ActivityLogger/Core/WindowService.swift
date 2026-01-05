import Cocoa
import CoreGraphics

struct WindowInfo {
    let appName: String
    let windowTitle: String
    let pid: Int
}

actor WindowService {
    
    func getActiveWindowInfo() -> WindowInfo? {
        // Simple approach: Get frontmost application
        guard let frontApp = NSWorkspace.shared.frontmostApplication else {
            return nil
        }
        
        let appName = frontApp.localizedName ?? "Unknown"
        let pid = Int(frontApp.processIdentifier)
        
        // To get window title, we need Accessibility API or CGWindowList (requires recording permission)
        // Trying AX API logic here
        let appElement = AXUIElementCreateApplication(pid_t(pid))
        
        var focusedWindow: AnyObject?
        let result = AXUIElementCopyAttributeValue(appElement, kAXFocusedWindowAttribute as CFString, &focusedWindow)
        
        var windowTitle = ""
        if result == .success, let window = focusedWindow as! AXUIElement? {
            var title: AnyObject?
            if AXUIElementCopyAttributeValue(window, kAXTitleAttribute as CFString, &title) == .success {
                windowTitle = title as? String ?? ""
            }
        }
        
        return WindowInfo(appName: appName, windowTitle: windowTitle, pid: pid)
    }
}
