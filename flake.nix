{
  description = "AutoGen Learning Project - Pure Nix reproducible environment";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};

        # Python environment with core dependencies
        pythonEnv = pkgs.python311.withPackages (ps: with ps; [
          # Essential Python packages
          pip
          setuptools
          wheel

          # Core dependencies available in nixpkgs
          aiohttp
          requests
          python-dotenv
          pydantic
          openai

          # Development tools
          ipython

          # Code quality and security tools
          black # Code formatter
          isort # Import sorter
          ruff # Fast linter (replaces flake8, pylint, etc.)
          mypy # Type checker
          bandit # Security linter
          safety # Dependency vulnerability scanner
        ]);

      in
      {
        devShells.default = pkgs.mkShell {
          buildInputs = [
            pythonEnv
            pkgs.git
            # Additional Nix-native tools
            pkgs.nixpkgs-fmt # Nix code formatter
            pkgs.deadnix # Dead code elimination for Nix
            pkgs.statix # Nix linter
            pkgs.vulnix # Nix security scanner
          ];

          # Set up a local pip environment for AutoGen packages
          shellHook = ''
            echo "🚀 AutoGen Pure Nix Environment"
            echo "==============================="
            
            # Create local Python environment
            export PYTHONPATH="$PWD:$PYTHONPATH"
            export PIP_PREFIX="$PWD/.pip-packages"
            export PYTHONPATH="$PIP_PREFIX/lib/python3.11/site-packages:$PYTHONPATH"
            export PATH="$PIP_PREFIX/bin:$PATH"
            
            # Create directories
            mkdir -p examples/{basic,intermediate,advanced}
            mkdir -p .pip-packages
            
            # Install AutoGen packages locally if not present
            if [ ! -d ".pip-packages/lib/python3.11/site-packages/autogen_agentchat" ]; then
              echo "📦 Installing AutoGen packages locally..."
              pip install --prefix="$PIP_PREFIX" --no-deps --disable-pip-version-check \
                "autogen-agentchat==0.6.1" \
                "autogen-ext[openai]==0.6.1" \
                "autogen-core==0.6.1" \
                "jsonref>=1.1.0" \
                "opentelemetry-api>=1.27.0" \
                "pillow>=11.0.0" \
                "protobuf>=5.29.3" \
                "tiktoken>=0.8.0" \
                "aiofiles" \
                "regex>=2022.1.18"
              echo "✅ AutoGen packages installed locally"
            fi
            
            echo ""
            echo "✅ Environment ready!"
            echo "📚 Quick start:"
            echo "   1. Copy env.example to .env and add your DeepSeek API key"
            echo "   2. Run: python examples/basic/01_hello_world.py"
            echo ""
            echo "🔧 Environment info:"
            echo "   • Python: $(python --version)"
            echo "   • Git: $(git --version)"
            echo "   • AutoGen packages: .pip-packages/"
            echo ""
            echo "🛠️  Code quality tools available:"
            echo "   • Format: make fmt (or: black . && isort . && nixpkgs-fmt flake.nix)"
            echo "   • Lint: make lint (or: ruff check . && mypy .)"
            echo "   • Security: make security (or: bandit -r . && safety check)"
            echo "   • All checks: make check"
          '';

          # Environment variables
          PYTHONPATH = ".";
        };

        # Convenience apps
        apps = {
          hello = {
            type = "app";
            program = "${pkgs.writeShellScript "run-hello" ''
              export PYTHONPATH="$PWD:.pip-packages/lib/python3.11/site-packages:$PYTHONPATH"
              cd ${self}
              ${pythonEnv}/bin/python examples/basic/01_hello_world.py
            ''}";
          };
        };
      });
}
