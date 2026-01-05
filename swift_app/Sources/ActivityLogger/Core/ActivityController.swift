import Foundation
import SwiftUI
import Observation

@MainActor
@Observable
class ActivityController {
    var isMonitoring = false
    var statusMessage = "Ready"
    var recentLogs: [String] = []
    
    // Services
    private let screenCaptureService = ScreenCaptureService()
    private let ocrService = OCRService()
    private let windowService = WindowService()
    private let logger = JsonlLogger()
    private let llmService = LLMService()
    private let speechService = SpeechService()
    
    private var timer: Timer?
    private let interval: TimeInterval = 2.0 // Default 2s
    
    init() {
        // Initialize services if needed
    }
    
    func startMonitoring() {
        guard !isMonitoring else { return }
        isMonitoring = true
        statusMessage = "Monitoring started"
        
        timer = Timer.scheduledTimer(withTimeInterval: interval, repeats: true) { [weak self] _ in
            Task {
                await self?.captureCycle()
            }
        }
    }
    
    func stopMonitoring() {
        timer?.invalidate()
        timer = nil
        isMonitoring = false
        statusMessage = "Monitoring stopped"
    }
    
    private func captureCycle() async {
        do {
            // 1. Window Info
            guard let windowInfo = await windowService.getActiveWindowInfo() else {
                return
            }
            
            // 2. Screen Capture
            let image = try await screenCaptureService.captureMainDisplay()
            
            // 3. OCR (Heavy)
            let text = try await ocrService.extractText(from: image)
            
            // 4. Log
            let timestamp = ISO8601DateFormatter().string(from: Date())
            let shortText = text.replacingOccurrences(of: "\n", with: " ").prefix(100)
            
            let entry = LogEntry(
                timestamp: timestamp,
                appName: windowInfo.appName,
                windowTitle: windowInfo.windowTitle,
                ocrText: text
            )
            
            logger.log(entry: entry)
            
            // 5. Update UI
            let logMsg = "[\(timestamp)] \(windowInfo.appName): \(shortText)..."
            self.recentLogs.insert(logMsg, at: 0)
            if self.recentLogs.count > 50 {
                self.recentLogs.removeLast()
            }
            
        } catch {
            print("Capture cycle error: \(error)")
            self.statusMessage = "Error: \(error.localizedDescription)"
        }
    }
}
