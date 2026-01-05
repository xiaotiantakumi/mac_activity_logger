import Foundation
import MLX
import MLXNN

public struct ModelArgs: Codable {
    public var hidden_size: Int = 2048
    public var intermediate_size: Int = 16384
    public var num_hidden_layers: Int = 18
    public var num_attention_heads: Int = 8
    public var num_key_value_heads: Int = 1
    public var head_dim: Int = 256
    public var rms_norm_eps: Float = 1e-6
    public var vocab_size: Int = 256000
    public var rope_theta: Float = 10000.0
}



class GemmaAttention: Module {
    let head_dim: Int
    let num_heads: Int
    let num_kv_heads: Int
    let scale: Float
    
    let q_proj: Linear
    let k_proj: Linear
    let v_proj: Linear
    let o_proj: Linear
    
    let rope: RoPE
    
    init(args: ModelArgs) {
        let dim = args.hidden_size
        self.num_heads = args.num_attention_heads
        self.num_kv_heads = args.num_key_value_heads
        self.head_dim = args.head_dim
        self.scale = 1.0 / sqrt(Float(head_dim))
        
        self.q_proj = Linear(dim, num_heads * head_dim, bias: false)
        self.k_proj = Linear(dim, num_kv_heads * head_dim, bias: false)
        self.v_proj = Linear(dim, num_kv_heads * head_dim, bias: false)
        self.o_proj = Linear(num_heads * head_dim, dim, bias: false)
        
        // RoPE (using default traditional=false, etc. or match Gemma config)
        self.rope = RoPE(dimensions: head_dim, traditional: false, base: args.rope_theta)
        
        super.init()
    }
    
    func callAsFunction(_ x: MLXArray, mask: MLXArray? = nil, cache: [MLXArray]? = nil) -> (MLXArray, MLXArray, MLXArray) {
        let B = x.shape[0]
        let L = x.shape[1]
        // let _ = x.shape[2] 
        
        var queries = q_proj(x)
        var keys = k_proj(x)
        var values = v_proj(x)
        
        // Reshape for attention
        queries = queries.reshaped([B, L, num_heads, head_dim]).transposed(0, 2, 1, 3) // B, H, L, D
        keys = keys.reshaped([B, L, num_kv_heads, head_dim]).transposed(0, 2, 1, 3)
        values = values.reshaped([B, L, num_kv_heads, head_dim]).transposed(0, 2, 1, 3)
        
        // RoPE
        queries = rope(queries)
        keys = rope(keys)
        
        // KV Cache handling would go here (omitted for brevity in this step, strictly prompt processing)
        // Standard Scaled Dot Product Attention
        let scores = (matmul(queries, keys.transposed(0, 1, 3, 2)) * scale)
        // Apply mask if needed
        let probs = softmax(scores, axis: -1)
        let output = matmul(probs, values).transposed(0, 2, 1, 3).reshaped([B, L, -1])
        
        return (o_proj(output), keys, values)
    }
}

class GemmaMLP: Module {
    let gate_proj: Linear
    let up_proj: Linear
    let down_proj: Linear
    
    init(args: ModelArgs) {
        let dim = args.hidden_size
        let hidden = args.intermediate_size
        self.gate_proj = Linear(dim, hidden, bias: false)
        self.up_proj = Linear(dim, hidden, bias: false)
        self.down_proj = Linear(hidden, dim, bias: false)
        super.init()
    }
    
    func callAsFunction(_ x: MLXArray) -> MLXArray {
        let gate = gate_proj(x)
        let up = up_proj(x)
        // GELU approximation used in Gemma
        return down_proj(gelu(gate) * up)
    }
}

class GemmaBlock: Module {
    let self_attn: GemmaAttention
    let mlp: GemmaMLP
    let input_layernorm: RMSNorm
    let post_attention_layernorm: RMSNorm
    
    init(args: ModelArgs) {
        self.self_attn = GemmaAttention(args: args)
        self.mlp = GemmaMLP(args: args)
        self.input_layernorm = RMSNorm(dimensions: args.hidden_size, eps: args.rms_norm_eps)
        self.post_attention_layernorm = RMSNorm(dimensions: args.hidden_size, eps: args.rms_norm_eps)
        super.init()
    }
    
    func callAsFunction(_ x: MLXArray) -> MLXArray {
        let (attn_out, _, _) = self_attn(input_layernorm(x)) // simplified return
        let h = x + attn_out
        return h + mlp(post_attention_layernorm(h))
    }
}

public class GemmaModel: Module {
    let embed_tokens: Embedding
    let layers: [GemmaBlock]
    let norm: RMSNorm
    
    public init(args: ModelArgs) {
        self.embed_tokens = Embedding(embeddingCount: args.vocab_size, dimensions: args.hidden_size)
        self.layers = (0..<args.num_hidden_layers).map { _ in GemmaBlock(args: args) }
        self.norm = RMSNorm(dimensions: args.hidden_size, eps: args.rms_norm_eps)
        super.init()
    }
    
    public func callAsFunction(_ x: MLXArray) -> MLXArray {
        var h = embed_tokens(x)
        // Scale embeddings (Gemma specific)
        h = h * sqrt(Float(h.dim(-1)))
        
        for layer in layers {
            h = layer(h)
        }
        return norm(h)
    }
}
