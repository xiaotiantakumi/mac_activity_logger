@preconcurrency import ScreenCaptureKit
import Cocoa

actor ScreenCaptureService {
    
    enum CaptureError: Error {
        case noDisplayFound
        case captureFailed(Error)
        case missingPermissions
    }
    
    static func checkPermissions() -> Bool {
        return CGPreflightScreenCaptureAccess()
    }
    
    static func requestPermissions() {
        CGRequestScreenCaptureAccess()
    }
    
    func captureMainDisplay() async throws -> CGImage {
        // 1. Get available content
        let content = try await SCShareableContent.current
        
        // 2. Find main display
        guard let mainDisplay = content.displays.first else {
            throw CaptureError.noDisplayFound
        }
        
        // 3. Create filter for the whole display
        let filter = SCContentFilter(display: mainDisplay, excludingApplications: [], exceptingWindows: [])
        
        // 4. Config
        let config = SCStreamConfiguration()
        config.width = mainDisplay.width
        config.height = mainDisplay.height
        config.showsCursor = true
        
        // 5. Capture (macOS 14+ API)
        let image = try await SCScreenshotManager.captureImage(contentFilter: filter, configuration: config)
        return image
    }
}
