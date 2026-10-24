import json
import os
import subprocess
import sys
import tempfile
import unittest

BASH = "C:/Program Files/Git/bin/bash.exe" if os.path.exists("C:/Program Files/Git/bin/bash.exe") else "bash"
HOOKS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "claude-code-config", ".claude", "hooks"))
VENV_SCRIPTS = os.path.abspath(os.path.join(HOOKS_DIR, "..", "..", "..", "..", "..", ".venv", "Scripts")).replace("\\", "/")
if not os.path.exists(VENV_SCRIPTS):
    VENV_SCRIPTS = "D:/Meta-OpenSource-Campaign/anthropic-oss-sprint/.venv/Scripts"

def get_env():
    env = os.environ.copy()
    if os.path.exists(VENV_SCRIPTS):
        env["PATH"] = VENV_SCRIPTS + os.pathsep + env.get("PATH", "")
    return env

class TestPreToolUseHooks(unittest.TestCase):
    def test_kill_switch_engaged(self):
        script = os.path.join(HOOKS_DIR, "kill-switch.sh").replace("\\", "/")
        with tempfile.TemporaryDirectory() as tmpdir:
            stop_file = os.path.join(tmpdir, "AGENT_STOP").replace("\\", "/")
            with open(stop_file, "w") as f:
                f.write("stop")
            
            env = get_env()
            env["AGENT_STOP_FILE"] = stop_file
            
            result = subprocess.run([BASH, script], capture_output=True, text=True, env=env)
            self.assertEqual(result.returncode, 0)
            data = json.loads(result.stdout.strip())
            
            self.assertIn("hookSpecificOutput", data)
            self.assertEqual(data["hookSpecificOutput"]["hookEventName"], "PreToolUse")
            self.assertEqual(data["hookSpecificOutput"]["permissionDecision"], "deny")
            self.assertIn("Kill switch engaged", data["hookSpecificOutput"]["permissionDecisionReason"])

    def test_kill_switch_not_engaged(self):
        script = os.path.join(HOOKS_DIR, "kill-switch.sh").replace("\\", "/")
        with tempfile.TemporaryDirectory() as tmpdir:
            stop_file = os.path.join(tmpdir, "AGENT_STOP").replace("\\", "/")
            
            env = get_env()
            env["AGENT_STOP_FILE"] = stop_file
            
            result = subprocess.run([BASH, script], capture_output=True, text=True, env=env)
            self.assertEqual(result.returncode, 0)
            self.assertEqual(result.stdout.strip(), "")

    def test_steer_with_content(self):
        script = os.path.join(HOOKS_DIR, "steer.sh").replace("\\", "/")
        with tempfile.TemporaryDirectory() as tmpdir:
            steer_file = os.path.join(tmpdir, "STEER.md").replace("\\", "/")
            with open(steer_file, "w") as f:
                f.write("Focus on authentication module first.")
            
            env = get_env()
            env["AGENT_STEER_FILE"] = steer_file
            
            result = subprocess.run([BASH, script], capture_output=True, text=True, env=env)
            self.assertEqual(result.returncode, 0)
            data = json.loads(result.stdout.strip())
            
            self.assertIn("hookSpecificOutput", data)
            self.assertEqual(data["hookSpecificOutput"]["hookEventName"], "PreToolUse")
            self.assertEqual(data["hookSpecificOutput"]["permissionDecision"], "deny")
            self.assertIn("OPERATOR STEERING: Focus on authentication module first.", data["hookSpecificOutput"]["permissionDecisionReason"])
            
            # Verify file was cleared
            self.assertEqual(os.path.getsize(steer_file), 0)

    def test_steer_empty_file(self):
        script = os.path.join(HOOKS_DIR, "steer.sh").replace("\\", "/")
        with tempfile.TemporaryDirectory() as tmpdir:
            steer_file = os.path.join(tmpdir, "STEER.md").replace("\\", "/")
            with open(steer_file, "w") as f:
                pass
            
            env = get_env()
            env["AGENT_STEER_FILE"] = steer_file
            
            result = subprocess.run([BASH, script], capture_output=True, text=True, env=env)
            self.assertEqual(result.returncode, 0)
            self.assertEqual(result.stdout.strip(), "")

    def test_verify_gate_blocked_without_evidence(self):
        script = os.path.join(HOOKS_DIR, "verify-gate.sh").replace("\\", "/")
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = os.path.join(tmpdir, ".evidence-reads").replace("\\", "/")
            
            env = get_env()
            env["VERIFY_READ_LOG"] = log_file
            env["RESULTS_FILE"] = "test-results.json"
            
            tool_input = json.dumps({"tool_input": {"file_path": "test-results.json"}})
            result = subprocess.run([BASH, script], input=tool_input, capture_output=True, text=True, env=env)
            self.assertEqual(result.returncode, 0)
            data = json.loads(result.stdout.strip())
            
            self.assertIn("hookSpecificOutput", data)
            self.assertEqual(data["hookSpecificOutput"]["hookEventName"], "PreToolUse")
            self.assertEqual(data["hookSpecificOutput"]["permissionDecision"], "deny")
            self.assertIn("Cannot modify the results file", data["hookSpecificOutput"]["permissionDecisionReason"])

    def test_verify_gate_allowed_with_evidence(self):
        script = os.path.join(HOOKS_DIR, "verify-gate.sh").replace("\\", "/")
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = os.path.join(tmpdir, ".evidence-reads").replace("\\", "/")
            with open(log_file, "w") as f:
                f.write("evidence.png\n")
            
            env = get_env()
            env["VERIFY_READ_LOG"] = log_file
            env["RESULTS_FILE"] = "test-results.json"
            
            tool_input = json.dumps({"tool_input": {"file_path": "test-results.json"}})
            result = subprocess.run([BASH, script], input=tool_input, capture_output=True, text=True, env=env)
            self.assertEqual(result.returncode, 0)
            self.assertEqual(result.stdout.strip(), "")
            # Log file is consumed
            self.assertEqual(os.path.getsize(log_file), 0)

if __name__ == "__main__":
    unittest.main()
