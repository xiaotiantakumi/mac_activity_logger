import Foundation
import Speech
import AVFoundation

@MainActor
class SpeechService: ObservableObject {
    private let speechRecognizer = SFSpeechRecognizer(locale: Locale(identifier: "ja-JP")) // Default to Japanese
    private var recognitionRequest: SFSpeechAudioBufferRecognitionRequest?
    private var recognitionTask: SFSpeechRecognitionTask?
    private let audioEngine = AVAudioEngine()
    
    @Published var isRecording = false
    @Published var transcribedText = ""
    @Published var errorMsg: String?
    
    init() {
        requestAuthorization()
    }
    
    private func requestAuthorization() {
        SFSpeechRecognizer.requestAuthorization { authStatus in
            Task { @MainActor in
                switch authStatus {
                case .authorized:
                    print("Speech recognition authorized")
                case .denied:
                    self.errorMsg = "Speech recognition authorization denied"
                case .restricted:
                    self.errorMsg = "Speech recognition restricted on this device"
                case .notDetermined:
                    self.errorMsg = "Speech recognition not yet authorized"
                @unknown default:
                    self.errorMsg = "Unknown authorization status"
                }
            }
        }
    }
    
    func startRecording() throws {
        // Cancel existing task if any
        if recognitionTask != nil {
            recognitionTask?.cancel()
            recognitionTask = nil
        }
        
        // AVAudioSession is not available on macOS
        // Note: AVAudioSession is primarily for iOS, on macOS implicit session is used or we configure AudioUnit manually if needed.
        // But for SFSpeechRecognizer on macOS, we just use AVAudioEngine.
        
        recognitionRequest = SFSpeechAudioBufferRecognitionRequest()
        
        guard let recognitionRequest = recognitionRequest else {
            throw SpeechError.requestInitFailed
        }
        
        // Enable on-device recognition if available (supports offline)
        if #available(macOS 14.0, *), speechRecognizer?.supportsOnDeviceRecognition == true {
             recognitionRequest.requiresOnDeviceRecognition = true
        } else {
             // Fallback or explicit false if older
             // recognitionRequest.requiresOnDeviceRecognition = false
        }
        
        recognitionRequest.shouldReportPartialResults = true
        
        let inputNode = audioEngine.inputNode
        
        recognitionTask = speechRecognizer?.recognitionTask(with: recognitionRequest) { result, error in
            var isFinal = false
            
            if let result = result {
                self.transcribedText = result.bestTranscription.formattedString
                isFinal = result.isFinal
            }
            
            if error != nil || isFinal {
                self.audioEngine.stop()
                inputNode.removeTap(onBus: 0)
                
                self.recognitionRequest = nil
                self.recognitionTask = nil
                self.isRecording = false
                
                if let error = error {
                    print("Recognition error: \(error.localizedDescription)")
                    self.errorMsg = error.localizedDescription
                }
            }
        }
        
        let recordingFormat = inputNode.outputFormat(forBus: 0)
        inputNode.installTap(onBus: 0, bufferSize: 1024, format: recordingFormat) { (buffer, when) in
            self.recognitionRequest?.append(buffer)
        }
        
        audioEngine.prepare()
        try audioEngine.start()
        
        isRecording = true
        errorMsg = nil
    }
    
    func stopRecording() {
        if audioEngine.isRunning {
            audioEngine.stop()
            recognitionRequest?.endAudio()
            isRecording = false
            // inputNode tap removal handled in completion block usually, but good to ensure
            audioEngine.inputNode.removeTap(onBus: 0)
        }
    }
}

enum SpeechError: Error {
    case requestInitFailed
}
