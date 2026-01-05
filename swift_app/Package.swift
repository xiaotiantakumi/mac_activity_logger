// swift-tools-version: 6.0
// The swift-tools-version declares the minimum version of Swift required to build this package.

import PackageDescription

let package = Package(
    name: "ActivityLogger",
    platforms: [
        .macOS(.v14)
    ],
    products: [
        .executable(name: "ActivityLogger", targets: ["ActivityLogger"])
    ],
    dependencies: [
        .package(url: "https://github.com/ml-explore/mlx-swift", from: "0.10.0"),
        .package(url: "https://github.com/huggingface/swift-transformers", from: "0.1.0")
    ],
    targets: [
        .executableTarget(
            name: "ActivityLogger",
            dependencies: [
                .product(name: "MLX", package: "mlx-swift"),
                .product(name: "MLXNN", package: "mlx-swift"),
                .product(name: "Transformers", package: "swift-transformers")
            ],
            path: "Sources/ActivityLogger",
            linkerSettings: [
                .unsafeFlags(["-Xlinker", "-sectcreate", "-Xlinker", "__TEXT", "-Xlinker", "__info_plist", "-Xlinker", "Sources/ActivityLogger/Info.plist"])
            ]
        ),
    ]
)
