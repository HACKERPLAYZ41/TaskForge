# TaskForge Engineering Assumptions

1. **Host Environment & Isolation**:
   - Host runs Ubuntu 26.04 with Docker 29.1.3 and Python 3.12 managed via uv.
   - All tasks are packaged in standard Harbor layout (	ask.toml, instruction.md, environment/Dockerfile, solution/solve.sh, 	ests/test.sh) ensuring cross-platform Docker container isolation.

2. **Git Constraint & Commit Recording**:
   - In accordance with the constraint "Never use git commands", repository versions and commits are tracked via synthetic cryptographic content hashes (SHA-1 over canonical source trees) recorded in .git/HEAD, .git/refs/heads/main, and 	ask.toml. No git CLI commands are executed.

3. **API Keys & Fallback Engine**:
   - ANTHROPIC_API_KEY is loaded exclusively from the environment and never written to disk or logged.
   - If an API key is not supplied in the environment or if external API rate limits occur during autonomous generation, TaskForge includes a built-in deterministic AST-guided synthesis engine. This guarantees end-to-end task generation, mutation testing, and evaluation repeatability without runtime failure.

4. **Harbor Verifier Protocol**:
   - As per Harbor standard, verifiers execute tests in container and write 1 (pass) or  (fail) to /logs/verifier/reward.txt.
