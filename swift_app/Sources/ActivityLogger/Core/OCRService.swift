import Vision
import Cocoa

actor OCRService {
    
    private let request: VNRecognizeTextRequest
    
    init() {
        self.request = VNRecognizeTextRequest()
        self.request.recognitionLevel = .accurate
        self.request.recognitionLanguages = ["ja-JP", "en-US"]
        self.request.usesLanguageCorrection = true
    }
    
    func extractText(from image: CGImage) async throws -> String {
        return try await withCheckedThrowingContinuation { continuation in
            let handler = VNImageRequestHandler(cgImage: image, options: [:])
            
            do {
                try handler.perform([self.request])
                
                guard let observations = self.request.results else {
                    continuation.resume(returning: "")
                    return
                }
                
                let text = observations.compactMap { $0.topCandidates(1).first?.string }.joined(separator: "\n")
                continuation.resume(returning: text)
                
            } catch {
                continuation.resume(throwing: error)
            }
        }
    }
}
