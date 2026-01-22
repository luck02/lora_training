# Security Audit Report: lora-training Repository

## Executive Summary

This LoRA fine-tuning pipeline has **1 critical security issue** (exposed API key), **2 high-severity issues** (path traversal and remote code execution risks), and several medium/low-severity findings. The codebase follows some good security practices but requires immediate attention to the critical issues.

---

## CRITICAL SEVERITY ISSUES

### 1. 🔴 Hardcoded API Key Exposed in .envrc

**Location**: `.envrc:2`

**Issue**: The file contains a plaintext Anthropic API key:
```bash
export ANTHROPIC_API_KEY="sk-ant-api03-XXXXXXXXXXXX..."  # REDACTED
```

**Risk**:
- **IMMEDIATE ACTION REQUIRED**: This API key can be used to make unauthorized API calls, incurring costs on your account
- Although `.envrc` is in `.gitignore` and was never committed to git, the key is exposed to:
  - Anyone with file system access to the repo
  - Backup systems
  - File sharing/cloud sync services
  - Accidental sharing of the directory

**Remediation**:
1. **IMMEDIATELY rotate this API key** in your Anthropic dashboard
2. Never store secrets in plaintext files
3. Use a password manager or secret management service
4. If using direnv, source from a secure external location or use encrypted secrets

---

## HIGH SEVERITY ISSUES

### 2. 🟠 Path Traversal Vulnerability in convert_vllm.py

**Location**: `scripts/convert_vllm.py:36-38`

**Issue**: User-supplied command-line argument `args.model` is used directly in file operations without validation:
```python
subprocess.run([
    "cp", "-r", args.model, output_dir
], check=True)
```

**Risk**:
- Attacker could provide malicious paths like `../../../etc/passwd` or `~/.ssh/`
- Could copy sensitive files to attacker-controlled locations
- Could overwrite critical system files

**Remediation**:
```python
# Validate and canonicalize paths
model_path = Path(args.model).resolve()
output_path = Path(output_dir).resolve()

# Ensure paths are within expected directories
if not str(model_path).startswith(str(Path.cwd())):
    raise ValueError("Model path must be within project directory")
```

### 3. 🟠 Remote Code Execution Risk with trust_remote_code=True

**Locations**:
- `scripts/train.py:62`
- `scripts/merge.py:40`

**Issue**: Loading models with `trust_remote_code=True` allows arbitrary Python code execution from HuggingFace Hub:
```python
model = AutoModelForCausalLM.from_pretrained(
    config["model"]["name"],
    ...
    trust_remote_code=True,  # ← Dangerous
)
```

**Risk**:
- Malicious model repositories can execute arbitrary code
- If model name is user-controlled or sourced from untrusted configs, attackers can point to malicious models
- Code runs with full Python interpreter privileges

**Remediation**:
1. Only load models from verified, trusted sources
2. Pin specific model versions/commits instead of branches
3. Consider removing `trust_remote_code=True` if the Qwen model doesn't require it
4. Validate model names against an allowlist in config

---

## MEDIUM SEVERITY ISSUES

### 4. 🟡 Insufficient Input Validation on File Paths

**Locations**: Multiple scripts

**Issue**: Command-line arguments and config file paths are used without validation:
- `scripts/train.py:44` - Config path not validated
- `scripts/generate_dataset.py:224` - Domain-based paths not sanitized
- `scripts/merge.py:30` - Output path not validated

**Risk**: Path traversal, directory traversal, arbitrary file read/write

**Remediation**: Validate all file paths against expected patterns and canonical paths

### 5. 🟡 Debug Files Written to Current Working Directory

**Location**: `scripts/generate_dataset.py:264-266, 301-303`

**Issue**: Debug files written without path sanitization:
```python
debug_output_path = Path(f"debug_raw_response_{idx}.txt")
with open(debug_output_path, "w") as f:
    f.write(response_text)
```

**Risk**:
- Clutters working directory
- No cleanup mechanism
- Could overwrite existing files
- Exposes potentially sensitive API responses

**Remediation**: Write debug files to a dedicated temp directory with proper permissions

### 6. 🟡 Shell Command Execution in capture_anthropic_responses.py

**Location**: `scripts/capture_anthropic_responses.py:22-23`

**Issue**: Uses shell=True equivalent with bash -c:
```python
result = subprocess.run(['bash', '-c', 'source .envrc && env'],
                       capture_output=True, text=True, check=True)
```

**Risk**: While not currently exploitable (no user input), this pattern is dangerous and could become vulnerable if modified

**Remediation**: Use python-dotenv or a safer environment loading mechanism

### 7. 🟡 Broad Exception Handling Masks Errors

**Locations**: Multiple files

**Issue**: Bare `except:` clauses without specific exception types:
- `scripts/json_parser_fix.py:48, 59, 84, 114, 154, 156`
- `scripts/generate_dataset.py:293, 305`

**Risk**: Masks unexpected errors, making debugging difficult and potentially hiding security issues

**Remediation**: Use specific exception types (e.g., `except json.JSONDecodeError:`)

---

## LOW SEVERITY ISSUES

### 8. 🟢 Unpinned Dependencies

**Location**: `requirements.txt`

**Issue**: Uses `>=` instead of `==` for version pinning:
```
torch>=2.0
transformers>=4.40
```

**Risk**: Future versions could introduce breaking changes or vulnerabilities

**Remediation**: Pin exact versions after testing, use tools like pip-tools

### 9. 🟢 Information Disclosure in Error Messages

**Locations**: Various scripts

**Issue**: Error messages expose internal paths and stack traces

**Risk**: Information leakage could aid attackers in reconnaissance

**Remediation**: Log detailed errors server-side, show generic messages to users

### 10. 🟢 No Rate Limiting on API Calls

**Location**: `scripts/generate_dataset.py` (live mode)

**Issue**: Sequential API calls without rate limiting (relies on SDK)

**Risk**: Could trigger rate limit errors or excessive costs

**Remediation**: Implement explicit rate limiting and backoff logic

---

## POSITIVE SECURITY PRACTICES ✅

1. **Environment Variables**: API key loaded from environment (though also hardcoded in .envrc)
2. **Safe YAML Loading**: Uses `yaml.safe_load()` instead of `yaml.load()`
3. **Gitignore Configured**: `.envrc`, `.env`, secrets properly excluded
4. **No Dangerous Functions**: No use of `eval()`, `exec()`, `pickle`, `marshal`
5. **Subprocess Safety**: Most subprocess calls use array format (not shell=True)
6. **4-bit Quantization**: Uses secure quantization methods
7. **No API Key in Git History**: Verified that `.envrc` was never committed

---

## RECOMMENDATIONS PRIORITY

### Immediate Actions (This Week)
1. **Rotate the exposed Anthropic API key immediately**
2. Remove `.envrc` from repo and use proper secret management
3. Add path validation to `convert_vllm.py`, `train.py`, `merge.py`

### Short Term (This Month)
4. Review necessity of `trust_remote_code=True`, add model name validation
5. Fix debug file writing to use proper temp directories
6. Replace bare `except:` with specific exception types
7. Add input validation for all command-line arguments

### Medium Term (Next Quarter)
8. Pin exact dependency versions in requirements.txt
9. Implement comprehensive logging with sanitized error messages
10. Add rate limiting and retry logic for API calls
11. Consider adding security scanning to CI/CD pipeline

---

## SECURITY TESTING RECOMMENDATIONS

1. **Static Analysis**: Run tools like `bandit`, `semgrep`, or `pylint --security`
2. **Dependency Scanning**: Use `pip-audit` or `safety` to check for known vulnerabilities
3. **Secret Scanning**: Use tools like `gitleaks` or `trufflehog` to scan history
4. **Fuzzing**: Test file parsing and input handling with unexpected inputs

---

## COMPLIANCE CONSIDERATIONS

If this code will handle production data or be deployed in regulated environments:
- Ensure API keys are rotated regularly
- Implement audit logging for all model training and API calls
- Consider data privacy implications of training data
- Document security controls for compliance (SOC 2, ISO 27001, etc.)

---

## Summary

**Total Issues Found**: 10 security issues (1 critical, 2 high, 3 medium, 4 low)

**Overall Risk Level**: **HIGH** (due to exposed API key)

**Immediate Action Required**: Yes - rotate API key and implement secret management

This codebase demonstrates good security awareness in some areas but requires immediate attention to the credential exposure and path validation issues before deployment or sharing.
