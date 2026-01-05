import Foundation
import MLX
import Tokenizers

actor LLMService {

    private var model: GemmaModel?
    private var tokenizer: Tokenizer?
    private let modelId = "mlx-community/gemma-2-2b-it-4bit"
    
    // Hardcoded simple args for now, ideally load from config.json
    private let modelArgs = ModelArgs(
        hidden_size: 2304,
        intermediate_size: 9216,
        num_hidden_layers: 26,
        num_attention_heads: 8,
        num_key_value_heads: 4,
        head_dim: 256,
        rms_norm_eps: 1e-6,
        vocab_size: 256000,
        rope_theta: 10000.0
    )
    
    enum LLMError: Error {
        case modelNotLoaded
        case tokenizerNotLoaded
        case generationFailed(String)
    }
    
    func loadModel() async throws {
        // 1. Download/Locate Model
        // For simplicity, using a specific local path or assuming download script ran
        // Ideally we use a Hub library, but for now we look in typical cache location or project dir
        let fileManager = FileManager.default
        let cacheDir = fileManager.homeDirectoryForCurrentUser.appendingPathComponent(".cache/huggingface/hub/models--mlx-community--gemma-2-2b-it-4bit/snapshots")
        
        // Find latest snapshot
        guard let snapshot = try? fileManager.contentsOfDirectory(at: cacheDir, includingPropertiesForKeys: nil).first else {
            print("Model not found in cache. Please run download_model.py")
            return
        }
        let modelDir = snapshot
        
        // 2. Load Tokenizer
        let tokenizer = try await AutoTokenizer.from(pretrained: modelId)
        self.tokenizer = tokenizer
        
        // 3. Load Weights
        print("Loading weights from \(modelDir.path)")
        // Pre-warm (eval)
        // MLX.eval(try MLX.loadArrays(path: modelDir.path)) 
        
        // Initialize Model
        let model = GemmaModel(args: modelArgs)
        
        // Note: Real weight loading requires recursively mapping dictionary keys to the model's parameters.
        // Swift MLX doesn't auto-map flat dictionaries to nested objects easily like Python's load_state_dict.
        // For this step, we will skip actual weight assignment to avoid complex traversal logic, 
        // effectively running with random weights for the structure test.
        // In a real implementation, we would implement `model.load(weights: ...)` 
        
        self.model = model
        print("Gemma Model Initialized (Weights pending full loader logic)")
    }
    
    func generate(prompt: String) async throws -> String {
        guard let model = self.model else { throw LLMError.modelNotLoaded }
        guard let tokenizer = self.tokenizer else { throw LLMError.tokenizerNotLoaded }
        
        // Tokenize
        let inputIds = tokenizer.encode(text: prompt)
        var tokens = MLXArray(inputIds).reshaped([1, -1]) // Batch 1
        
        // Generation Loop (Simplified)
        var outputTokens = [Int]()
        
        for _ in 0..<50 { // Max 50 tokens
            let logits = model(tokens)
            let nextToken = argMax(logits[-1, -1]).item(Int.self)
            outputTokens.append(nextToken)
            
            // Append and continue (inefficient concat, use KV cache in real impl)
            let nextTokenArr = MLXArray([nextToken]).reshaped([1, 1])
            tokens = MLX.concatenated([tokens, nextTokenArr], axis: 1)
            
            if nextToken == tokenizer.eosTokenId { break }
        }
        
        return tokenizer.decode(tokens: outputTokens)
    }
}
