import Foundation

struct LogEntry: Codable {
    let timestamp: String
    let appName: String
    let windowTitle: String
    let ocrText: String
    // Add other fields as needed
}

class JsonlLogger {
    private let fileManager = FileManager.default
    private var currentFileHandle: FileHandle?
    private var currentDateString: String = ""
    private let logsDirectory: URL
    
    init() {
        // Default to ~/Documents/mac_logs
        let documents = fileManager.urls(for: .documentDirectory, in: .userDomainMask).first!
        self.logsDirectory = documents.appendingPathComponent("mac_logs")
        try? fileManager.createDirectory(at: logsDirectory, withIntermediateDirectories: true)
    }
    
    func log(entry: LogEntry) {
        let date = Date()
        let formatter = DateFormatter()
        formatter.dateFormat = "yyyy-MM-dd"
        let dateString = formatter.string(from: date)
        
        if dateString != currentDateString {
            rotateFile(dateString: dateString)
        }
        
        guard let fileHandle = currentFileHandle else { return }
        
        let encoder = JSONEncoder()
        encoder.outputFormatting = .sortedKeys
        
        do {
            let data = try encoder.encode(entry)
            fileHandle.seekToEndOfFile()
            fileHandle.write(data)
            fileHandle.write("\n".data(using: .utf8)!)
        } catch {
            print("Failed to write log entry: \(error)")
        }
    }
    
    private func rotateFile(dateString: String) {
        if let handle = currentFileHandle {
            try? handle.close()
        }
        
        // Create daily directory: logs/YYYY-MM-dd/
        let dailyDir = logsDirectory.appendingPathComponent(dateString)
        try? fileManager.createDirectory(at: dailyDir, withIntermediateDirectories: true)
        
        let fileURL = dailyDir.appendingPathComponent("activity_log.jsonl")
        
        if !fileManager.fileExists(atPath: fileURL.path) {
            fileManager.createFile(atPath: fileURL.path, contents: nil)
        }
        
        do {
            currentFileHandle = try FileHandle(forWritingTo: fileURL)
            currentDateString = dateString
        } catch {
            print("Failed to open log file: \(error)")
        }
    }
}
