# Updating

Use:

```bash
./wsl/06-update-existing-workspace.sh
```

v0.6 keeps the v0.5 minimal manifest and changes the primary UI to one Copilot Chat surface. Migration removes the old `workflow-glm-copilot` helper, installs Codex Bridge, preserves the dedicated GLM provider, keeps the official Codex extension as fallback, and leaves credentials untouched in VS Code SecretStorage.

Version markers are written only after the main install and doctor stages succeed.
