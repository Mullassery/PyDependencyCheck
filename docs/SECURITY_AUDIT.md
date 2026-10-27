# Security Vulnerability Audit - PyDependencyCheck

**Audit Date:** 2026-10-27
**Repository:** /Users/georgimullassery/Desktop/Projects/PyDependencyCheck
**Total Findings:** 199

## Summary
- **Critical:** 159
- **High:** 2
- **Medium:** 38

## Findings

### 1. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/_pytest/_code/code.py:164
- **Description:** eval()
- **Evidence (Line):** `def eval(self, code, **vars):`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 2. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/_pytest/_code/code.py:173
- **Description:** eval()
- **Evidence (Line):** `return eval(code, self.f_globals, f_locals)`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 3. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/_pytest/_code/code.py:326
- **Description:** eval()
- **Evidence (Line):** `# however via `exec(...)` / `eval(...)` they can be other types`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 4. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/_pytest/_code/code.py:326
- **Description:** exec()
- **Evidence (Line):** `# however via `exec(...)` / `eval(...)` they can be other types`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 5. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/_pytest/_py/path.py:1153
- **Description:** exec()
- **Evidence (Line):** `exec(f.read(), mod.__dict__)`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 6. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/_pytest/_py/path.py:1159
- **Description:** exec()
- **Evidence (Line):** `def sysexec(self, *argv: os.PathLike[str], **popen_opts: Any) -> str:`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 7. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/_pytest/assertion/rewrite.py:188
- **Description:** exec()
- **Evidence (Line):** `exec(co, module.__dict__)`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 8. [Critical] Insecure Deserialization
- **File:** .venv-test/lib/python3.12/site-packages/_pytest/assertion/rewrite.py:393
- **Description:** marshal load
- **Evidence (Line):** `co = marshal.load(fp)`
- **Exploit Scenario:** Attacker could achieve remote code execution
- **Fix Recommendation:** Use safe serialization formats (JSON), avoid pickle/yaml.load with untrusted data
- **Confidence:** High

### 9. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/_pytest/capture.py:1112
- **Description:** os.system()
- **Evidence (Line):** `os.system('echo "hello"')`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 10. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/_pytest/capture.py:1140
- **Description:** os.system()
- **Evidence (Line):** `os.system('echo "hello"')`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 11. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/_pytest/mark/__init__.py:66
- **Description:** eval()
- **Evidence (Line):** `def test_eval(test_input, expected):`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 12. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/_pytest/mark/__init__.py:67
- **Description:** eval()
- **Evidence (Line):** `assert eval(test_input) == expected`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 13. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/_pytest/mark/expression.py:295
- **Description:** eval()
- **Evidence (Line):** `"""Adapts a matcher function to a locals mapping as required by eval()."""`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 14. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/_pytest/mark/expression.py:353
- **Description:** eval()
- **Evidence (Line):** `return bool(eval(self._code, {"__builtins__": {}}, MatcherAdapter(matcher)))`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 15. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/_pytest/pytester.py:296
- **Description:** eval()
- **Evidence (Line):** `if eval(check, backlocals, call.__dict__):`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 16. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/_pytest/skipping.py:92
- **Description:** eval()
- **Evidence (Line):** `If an old-style string condition is given, it is eval()'d, otherwise the`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 17. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/_pytest/skipping.py:119
- **Description:** eval()
- **Evidence (Line):** `result = eval(condition_code, globals_)`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 18. [Critical] Insecure Deserialization
- **File:** .venv-test/lib/python3.12/site-packages/black/cache.py:80
- **Description:** pickle load/dumps
- **Evidence (Line):** `data: dict[str, tuple[float, int, str]] = pickle.load(fobj)`
- **Exploit Scenario:** Attacker could achieve remote code execution
- **Fix Recommendation:** Use safe serialization formats (JSON), avoid pickle/yaml.load with untrusted data
- **Confidence:** High

### 19. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/blib2to3/Grammar.txt:9
- **Description:** eval()
- **Evidence (Line):** `#	eval_input is the input for the eval() and input() functions.`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 20. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/blib2to3/pgen2/conv.py:186
- **Description:** eval()
- **Evidence (Line):** `rawbitset = eval(mo.group(1))`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 21. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/blib2to3/pgen2/conv.py:212
- **Description:** eval()
- **Evidence (Line):** `y = eval(y)`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 22. [Critical] Insecure Deserialization
- **File:** .venv-test/lib/python3.12/site-packages/blib2to3/pgen2/grammar.py:124
- **Description:** pickle load/dumps
- **Evidence (Line):** `d = pickle.load(f)`
- **Exploit Scenario:** Attacker could achieve remote code execution
- **Fix Recommendation:** Use safe serialization formats (JSON), avoid pickle/yaml.load with untrusted data
- **Confidence:** High

### 23. [Critical] Insecure Deserialization
- **File:** .venv-test/lib/python3.12/site-packages/blib2to3/pgen2/grammar.py:129
- **Description:** pickle load/dumps
- **Evidence (Line):** `self._update(pickle.loads(pkl))`
- **Exploit Scenario:** Attacker could achieve remote code execution
- **Fix Recommendation:** Use safe serialization formats (JSON), avoid pickle/yaml.load with untrusted data
- **Confidence:** High

### 24. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/blib2to3/pgen2/literals.py:4
- **Description:** eval()
- **Evidence (Line):** `"""Safely evaluate Python string literals without using eval()."""`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 25. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/blib2to3/pgen2/pgen.py:100
- **Description:** eval()
- **Evidence (Line):** `value = eval(label)`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 26. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/cffi/_cffi_gen_src.py:53
- **Description:** exec()
- **Evidence (Line):** `exec(compiled, globs, globs)`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 27. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/cffi/recompiler.py:80
- **Description:** eval()
- **Evidence (Line):** `flags = eval(self.flags, G_FLAGS)`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 28. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/cffi/setuptools_ext.py:26
- **Description:** exec()
- **Evidence (Line):** `exec(code, glob, glob)`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 29. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/coverage/execfile.py:222
- **Description:** exec()
- **Evidence (Line):** `exec(code, main_mod.__dict__)`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 30. [Critical] Insecure Deserialization
- **File:** .venv-test/lib/python3.12/site-packages/coverage/execfile.py:335
- **Description:** marshal load
- **Evidence (Line):** `code = marshal.load(fpyc)`
- **Exploit Scenario:** Attacker could achieve remote code execution
- **Fix Recommendation:** Use safe serialization formats (JSON), avoid pickle/yaml.load with untrusted data
- **Confidence:** High

### 31. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/coverage/htmlfiles/coverage_html.js:236
- **Description:** exec()
- **Evidence (Line):** `const match = /\.([0-9]+)/.exec(cell.textContent);`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 32. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/coverage/parser.py:691
- **Description:** eval()
- **Evidence (Line):** `return True, eval(node.id)  # pylint: disable=eval-used`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 33. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/coverage/templite.py:70
- **Description:** exec()
- **Evidence (Line):** `exec(python_source, global_namespace)`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 34. [Critical] Hardcoded Secret
- **File:** .venv-test/lib/python3.12/site-packages/cryptography/hazmat/_oid.py:372
- **Description:** Password Assignment detected
- **Evidence (Line):** `AttributeOID.CHALLENGE_PASSWORD: "challengePassword",`
- **Exploit Scenario:** Attacker could extract credentials and gain unauthorized access
- **Fix Recommendation:** Move secrets to environment variables or secret manager, rotate compromised credentials
- **Confidence:** High

### 35. [Critical] Hardcoded Secret
- **File:** .venv-test/lib/python3.12/site-packages/cryptography/hazmat/primitives/serialization/ssh.py:77
- **Description:** Private Key detected
- **Evidence (Line):** `_SK_START = b"-----BEGIN OPENSSH PRIVATE KEY-----"`
- **Exploit Scenario:** Attacker could extract credentials and gain unauthorized access
- **Fix Recommendation:** Move secrets to environment variables or secret manager, rotate compromised credentials
- **Confidence:** High

### 36. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/git/util.py:456
- **Description:** exec()
- **Evidence (Line):** `def is_exec(fpath: str) -> bool:`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 37. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/git/util.py:473
- **Description:** exec()
- **Evidence (Line):** `if is_exec(f):`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 38. [Critical] Hardcoded Secret
- **File:** .venv-test/lib/python3.12/site-packages/grpc/_server.py:64
- **Description:** Token Assignment detected
- **Evidence (Line):** `_RECEIVE_CLOSE_ON_SERVER_TOKEN = "receive_close_on_server"`
- **Exploit Scenario:** Attacker could extract credentials and gain unauthorized access
- **Fix Recommendation:** Move secrets to environment variables or secret manager, rotate compromised credentials
- **Confidence:** High

### 39. [Critical] Hardcoded Secret
- **File:** .venv-test/lib/python3.12/site-packages/grpc/_server.py:65
- **Description:** Token Assignment detected
- **Evidence (Line):** `_SEND_INITIAL_METADATA_TOKEN = "send_initial_metadata"`
- **Exploit Scenario:** Attacker could extract credentials and gain unauthorized access
- **Fix Recommendation:** Move secrets to environment variables or secret manager, rotate compromised credentials
- **Confidence:** High

### 40. [Critical] Hardcoded Secret
- **File:** .venv-test/lib/python3.12/site-packages/grpc/_server.py:71
- **Description:** Token Assignment detected
- **Evidence (Line):** `_SEND_STATUS_FROM_SERVER_TOKEN = "send_status_from_server"`
- **Exploit Scenario:** Attacker could extract credentials and gain unauthorized access
- **Fix Recommendation:** Move secrets to environment variables or secret manager, rotate compromised credentials
- **Confidence:** High

### 41. [Critical] Insecure Deserialization
- **File:** .venv-test/lib/python3.12/site-packages/jinja2/bccache.py:73
- **Description:** pickle load/dumps
- **Evidence (Line):** `checksum = pickle.load(f)`
- **Exploit Scenario:** Attacker could achieve remote code execution
- **Fix Recommendation:** Use safe serialization formats (JSON), avoid pickle/yaml.load with untrusted data
- **Confidence:** High

### 42. [Critical] Insecure Deserialization
- **File:** .venv-test/lib/python3.12/site-packages/jinja2/bccache.py:79
- **Description:** marshal load
- **Evidence (Line):** `self.code = marshal.load(f)`
- **Exploit Scenario:** Attacker could achieve remote code execution
- **Fix Recommendation:** Use safe serialization formats (JSON), avoid pickle/yaml.load with untrusted data
- **Confidence:** High

### 43. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/jinja2/debug.py:145
- **Description:** exec()
- **Evidence (Line):** `exec(code, globals, locals)`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 44. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/jinja2/environment.py:1228
- **Description:** exec()
- **Evidence (Line):** `exec(code, namespace)`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 45. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/jinja2/lexer.py:663
- **Description:** eval()
- **Evidence (Line):** `value = literal_eval(value_str.replace("_", ""))`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 46. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/jinja2/nativetypes.py:40
- **Description:** eval()
- **Evidence (Line):** `return literal_eval(`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 47. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/jinja2/nodes.py:581
- **Description:** eval()
- **Evidence (Line):** `representation (objects where ``eval(repr(x)) == x`` is true).`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 48. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/mypy/dmypy/client.py:556
- **Description:** os.system()
- **Evidence (Line):** `os.system("")`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 49. [Critical] Insecure Deserialization
- **File:** .venv-test/lib/python3.12/site-packages/mypy/dmypy/client.py:624
- **Description:** pickle load/dumps
- **Evidence (Line):** `options_dict = pickle.loads(b64decode(args.options_data))`
- **Exploit Scenario:** Attacker could achieve remote code execution
- **Fix Recommendation:** Use safe serialization formats (JSON), avoid pickle/yaml.load with untrusted data
- **Confidence:** High

### 50. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/mypy/evalexpr.py:30
- **Description:** eval()
- **Evidence (Line):** `return ast.literal_eval(f"b'{o.value}'")`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 51. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/mypy/evalexpr.py:32
- **Description:** eval()
- **Evidence (Line):** `return ast.literal_eval(f'b"{o.value}"')`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 52. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/mypy/modulefinder.py:864
- **Description:** eval()
- **Evidence (Line):** `sys_path, site_packages = ast.literal_eval(`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 53. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/mypy/test/testdaemon.py:89
- **Description:** subprocess with shell=True
- **Evidence (Line):** `output = subprocess.check_output(`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 54. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/mypyc/test/test_run.py:465
- **Description:** eval()
- **Evidence (Line):** `return ast.literal_eval(m.group(1))`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 55. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/mypyc/test/test_run.py:134
- **Description:** exec()
- **Evidence (Line):** `exec(f.read(), g)`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 56. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/networkx/algorithms/bipartite/edgelist.py:288
- **Description:** eval()
- **Evidence (Line):** `edgedata = dict(literal_eval(" ".join(d)))`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 57. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/networkx/algorithms/bipartite/tests/test_community.py:183
- **Description:** eval()
- **Evidence (Line):** `def _q_merge_delta_via_full_eval(G, C_a, C_b, rest, red, resolution=1, weight="weight"):`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 58. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/networkx/algorithms/bipartite/tests/test_community.py:206
- **Description:** eval()
- **Evidence (Line):** `q_delta = _q_merge_delta_via_full_eval(G, {u}, B, [{1, 2, 3}], red)`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 59. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/networkx/algorithms/bipartite/tests/test_community.py:219
- **Description:** eval()
- **Evidence (Line):** `q_delta = _q_merge_delta_via_full_eval(G, {u}, B, [{0, 1, 3}], red)`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 60. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/networkx/algorithms/bipartite/tests/test_community.py:236
- **Description:** eval()
- **Evidence (Line):** `q_delta = _q_merge_delta_via_full_eval(G, A, B, [], red)`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 61. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/networkx/algorithms/bipartite/tests/test_community.py:253
- **Description:** eval()
- **Evidence (Line):** `q_delta = _q_merge_delta_via_full_eval(G, A, B, [], red)`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 62. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/networkx/algorithms/bipartite/tests/test_community.py:268
- **Description:** eval()
- **Evidence (Line):** `q_delta = _q_merge_delta_via_full_eval(G, A, B, [], red, resolution=gamma)`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 63. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/networkx/algorithms/bipartite/tests/test_community.py:288
- **Description:** eval()
- **Evidence (Line):** `q_delta = _q_merge_delta_via_full_eval(G, A, B, rest, red)`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 64. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/networkx/algorithms/bipartite/tests/test_community.py:308
- **Description:** eval()
- **Evidence (Line):** `q_delta = _q_merge_delta_via_full_eval(G, A, B, [], red)`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 65. [Critical] Insecure Deserialization
- **File:** .venv-test/lib/python3.12/site-packages/networkx/algorithms/flow/tests/test_maxflow_large_graph.py:56
- **Description:** pickle load/dumps
- **Evidence (Line):** `G = pickle.load(f)`
- **Exploit Scenario:** Attacker could achieve remote code execution
- **Fix Recommendation:** Use safe serialization formats (JSON), avoid pickle/yaml.load with untrusted data
- **Confidence:** High

### 66. [Critical] Insecure Deserialization
- **File:** .venv-test/lib/python3.12/site-packages/networkx/algorithms/flow/tests/test_mincost.py:469
- **Description:** pickle load/dumps
- **Evidence (Line):** `G = pickle.load(f)`
- **Exploit Scenario:** Attacker could achieve remote code execution
- **Fix Recommendation:** Use safe serialization formats (JSON), avoid pickle/yaml.load with untrusted data
- **Confidence:** High

### 67. [Critical] Insecure Deserialization
- **File:** .venv-test/lib/python3.12/site-packages/networkx/algorithms/flow/tests/test_networksimplex.py:180
- **Description:** pickle load/dumps
- **Evidence (Line):** `G = pickle.load(f)`
- **Exploit Scenario:** Attacker could achieve remote code execution
- **Fix Recommendation:** Use safe serialization formats (JSON), avoid pickle/yaml.load with untrusted data
- **Confidence:** High

### 68. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/networkx/algorithms/operators/tests/test_all.py:28
- **Description:** eval()
- **Evidence (Line):** `assert ghj.nodes[n] == eval(graph).nodes[int(node)]`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 69. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/networkx/algorithms/operators/tests/test_binary.py:23
- **Description:** eval()
- **Evidence (Line):** `assert gh.nodes[n] == eval(graph).nodes[int(node)]`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 70. [Critical] Insecure Deserialization
- **File:** .venv-test/lib/python3.12/site-packages/networkx/classes/tests/test_coreviews.py:16
- **Description:** pickle load/dumps
- **Evidence (Line):** `pview = pickle.loads(pickle.dumps(view, -1))`
- **Exploit Scenario:** Attacker could achieve remote code execution
- **Fix Recommendation:** Use safe serialization formats (JSON), avoid pickle/yaml.load with untrusted data
- **Confidence:** High

### 71. [Critical] Insecure Deserialization
- **File:** .venv-test/lib/python3.12/site-packages/networkx/classes/tests/test_coreviews.py:19
- **Description:** pickle load/dumps
- **Evidence (Line):** `pview = pickle.loads(pickle.dumps(view))`
- **Exploit Scenario:** Attacker could achieve remote code execution
- **Fix Recommendation:** Use safe serialization formats (JSON), avoid pickle/yaml.load with untrusted data
- **Confidence:** High

### 72. [Critical] Insecure Deserialization
- **File:** .venv-test/lib/python3.12/site-packages/networkx/classes/tests/test_coreviews.py:73
- **Description:** pickle load/dumps
- **Evidence (Line):** `pview = pickle.loads(pickle.dumps(view, -1))`
- **Exploit Scenario:** Attacker could achieve remote code execution
- **Fix Recommendation:** Use safe serialization formats (JSON), avoid pickle/yaml.load with untrusted data
- **Confidence:** High

### 73. [Critical] Insecure Deserialization
- **File:** .venv-test/lib/python3.12/site-packages/networkx/classes/tests/test_coreviews.py:153
- **Description:** pickle load/dumps
- **Evidence (Line):** `pview = pickle.loads(pickle.dumps(view, -1))`
- **Exploit Scenario:** Attacker could achieve remote code execution
- **Fix Recommendation:** Use safe serialization formats (JSON), avoid pickle/yaml.load with untrusted data
- **Confidence:** High

### 74. [Critical] Insecure Deserialization
- **File:** .venv-test/lib/python3.12/site-packages/networkx/classes/tests/test_coreviews.py:211
- **Description:** pickle load/dumps
- **Evidence (Line):** `pview = pickle.loads(pickle.dumps(view, -1))`
- **Exploit Scenario:** Attacker could achieve remote code execution
- **Fix Recommendation:** Use safe serialization formats (JSON), avoid pickle/yaml.load with untrusted data
- **Confidence:** High

### 75. [Critical] Insecure Deserialization
- **File:** .venv-test/lib/python3.12/site-packages/networkx/classes/tests/test_graph.py:268
- **Description:** pickle load/dumps
- **Evidence (Line):** `H = pickle.loads(pickle.dumps(G, -1))`
- **Exploit Scenario:** Attacker could achieve remote code execution
- **Fix Recommendation:** Use safe serialization formats (JSON), avoid pickle/yaml.load with untrusted data
- **Confidence:** High

### 76. [Critical] Insecure Deserialization
- **File:** .venv-test/lib/python3.12/site-packages/networkx/classes/tests/test_graph.py:677
- **Description:** pickle load/dumps
- **Evidence (Line):** `pg = pickle.loads(pickle.dumps(G, -1))`
- **Exploit Scenario:** Attacker could achieve remote code execution
- **Fix Recommendation:** Use safe serialization formats (JSON), avoid pickle/yaml.load with untrusted data
- **Confidence:** High

### 77. [Critical] Insecure Deserialization
- **File:** .venv-test/lib/python3.12/site-packages/networkx/classes/tests/test_graph.py:679
- **Description:** pickle load/dumps
- **Evidence (Line):** `pg = pickle.loads(pickle.dumps(G))`
- **Exploit Scenario:** Attacker could achieve remote code execution
- **Fix Recommendation:** Use safe serialization formats (JSON), avoid pickle/yaml.load with untrusted data
- **Confidence:** High

### 78. [Critical] Insecure Deserialization
- **File:** .venv-test/lib/python3.12/site-packages/networkx/classes/tests/test_graphviews.py:18
- **Description:** pickle load/dumps
- **Evidence (Line):** `prv = pickle.loads(pickle.dumps(rv, -1))`
- **Exploit Scenario:** Attacker could achieve remote code execution
- **Fix Recommendation:** Use safe serialization formats (JSON), avoid pickle/yaml.load with untrusted data
- **Confidence:** High

### 79. [Critical] Insecure Deserialization
- **File:** .venv-test/lib/python3.12/site-packages/networkx/classes/tests/test_graphviews.py:65
- **Description:** pickle load/dumps
- **Evidence (Line):** `prv = pickle.loads(pickle.dumps(rv, -1))`
- **Exploit Scenario:** Attacker could achieve remote code execution
- **Fix Recommendation:** Use safe serialization formats (JSON), avoid pickle/yaml.load with untrusted data
- **Confidence:** High

### 80. [Critical] Insecure Deserialization
- **File:** .venv-test/lib/python3.12/site-packages/networkx/classes/tests/test_graphviews.py:118
- **Description:** pickle load/dumps
- **Evidence (Line):** `pdv = pickle.loads(pickle.dumps(dv, -1))`
- **Exploit Scenario:** Attacker could achieve remote code execution
- **Fix Recommendation:** Use safe serialization formats (JSON), avoid pickle/yaml.load with untrusted data
- **Confidence:** High

### 81. [Critical] Insecure Deserialization
- **File:** .venv-test/lib/python3.12/site-packages/networkx/classes/tests/test_graphviews.py:157
- **Description:** pickle load/dumps
- **Evidence (Line):** `puv = pickle.loads(pickle.dumps(uv, -1))`
- **Exploit Scenario:** Attacker could achieve remote code execution
- **Fix Recommendation:** Use safe serialization formats (JSON), avoid pickle/yaml.load with untrusted data
- **Confidence:** High

### 82. [Critical] Insecure Deserialization
- **File:** .venv-test/lib/python3.12/site-packages/networkx/classes/tests/test_graphviews.py:206
- **Description:** pickle load/dumps
- **Evidence (Line):** `H = pickle.loads(pickle.dumps(G, -1))`
- **Exploit Scenario:** Attacker could achieve remote code execution
- **Fix Recommendation:** Use safe serialization formats (JSON), avoid pickle/yaml.load with untrusted data
- **Confidence:** High

### 83. [Critical] Insecure Deserialization
- **File:** .venv-test/lib/python3.12/site-packages/networkx/classes/tests/test_reportviews.py:22
- **Description:** pickle load/dumps
- **Evidence (Line):** `pnv = pickle.loads(pickle.dumps(nv, -1))`
- **Exploit Scenario:** Attacker could achieve remote code execution
- **Fix Recommendation:** Use safe serialization formats (JSON), avoid pickle/yaml.load with untrusted data
- **Confidence:** High

### 84. [Critical] Insecure Deserialization
- **File:** .venv-test/lib/python3.12/site-packages/networkx/classes/tests/test_reportviews.py:93
- **Description:** pickle load/dumps
- **Evidence (Line):** `pnv = pickle.loads(pickle.dumps(nv, -1))`
- **Exploit Scenario:** Attacker could achieve remote code execution
- **Fix Recommendation:** Use safe serialization formats (JSON), avoid pickle/yaml.load with untrusted data
- **Confidence:** High

### 85. [Critical] Insecure Deserialization
- **File:** .venv-test/lib/python3.12/site-packages/networkx/classes/tests/test_reportviews.py:278
- **Description:** pickle load/dumps
- **Evidence (Line):** `pev = pickle.loads(pickle.dumps(ev, -1))`
- **Exploit Scenario:** Attacker could achieve remote code execution
- **Fix Recommendation:** Use safe serialization formats (JSON), avoid pickle/yaml.load with untrusted data
- **Confidence:** High

### 86. [Critical] Insecure Deserialization
- **File:** .venv-test/lib/python3.12/site-packages/networkx/classes/tests/test_reportviews.py:568
- **Description:** pickle load/dumps
- **Evidence (Line):** `pev = pickle.loads(pickle.dumps(ev, -1))`
- **Exploit Scenario:** Attacker could achieve remote code execution
- **Fix Recommendation:** Use safe serialization formats (JSON), avoid pickle/yaml.load with untrusted data
- **Confidence:** High

### 87. [Critical] Insecure Deserialization
- **File:** .venv-test/lib/python3.12/site-packages/networkx/classes/tests/test_reportviews.py:1027
- **Description:** pickle load/dumps
- **Evidence (Line):** `pdeg = pickle.loads(pickle.dumps(deg, -1))`
- **Exploit Scenario:** Attacker could achieve remote code execution
- **Fix Recommendation:** Use safe serialization formats (JSON), avoid pickle/yaml.load with untrusted data
- **Confidence:** High

### 88. [Critical] Insecure Deserialization
- **File:** .venv-test/lib/python3.12/site-packages/networkx/classes/tests/test_reportviews.py:1416
- **Description:** pickle load/dumps
- **Evidence (Line):** `pickle.loads(pickle.dumps(G, -1))`
- **Exploit Scenario:** Attacker could achieve remote code execution
- **Fix Recommendation:** Use safe serialization formats (JSON), avoid pickle/yaml.load with untrusted data
- **Confidence:** High

### 89. [Critical] Insecure Deserialization
- **File:** .venv-test/lib/python3.12/site-packages/networkx/classes/tests/test_reportviews.py:1427
- **Description:** pickle load/dumps
- **Evidence (Line):** `ev = pickle.loads(pickle.dumps(G.edges, -1))`
- **Exploit Scenario:** Attacker could achieve remote code execution
- **Fix Recommendation:** Use safe serialization formats (JSON), avoid pickle/yaml.load with untrusted data
- **Confidence:** High

### 90. [Critical] Insecure Deserialization
- **File:** .venv-test/lib/python3.12/site-packages/networkx/classes/tests/test_reportviews.py:1430
- **Description:** pickle load/dumps
- **Evidence (Line):** `dv = pickle.loads(pickle.dumps(G.degree, -1))`
- **Exploit Scenario:** Attacker could achieve remote code execution
- **Fix Recommendation:** Use safe serialization formats (JSON), avoid pickle/yaml.load with untrusted data
- **Confidence:** High

### 91. [Critical] Insecure Deserialization
- **File:** .venv-test/lib/python3.12/site-packages/networkx/classes/tests/test_reportviews.py:1434
- **Description:** pickle load/dumps
- **Evidence (Line):** `ev = pickle.loads(pickle.dumps(graph_class([(0, 1), (1, 2)]).edges, -1))`
- **Exploit Scenario:** Attacker could achieve remote code execution
- **Fix Recommendation:** Use safe serialization formats (JSON), avoid pickle/yaml.load with untrusted data
- **Confidence:** High

### 92. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/networkx/readwrite/edgelist.py:316
- **Description:** eval()
- **Evidence (Line):** `edgedata = dict(literal_eval(edgedata_str.strip()))`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 93. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/networkx/readwrite/gml.py:106
- **Description:** eval()
- **Evidence (Line):** `return literal_eval(rep)`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 94. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/networkx/readwrite/multiline_adjlist.py:324
- **Description:** eval()
- **Evidence (Line):** `edgedata = literal_eval(data)`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 95. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/networkx/readwrite/tests/test_gml.py:454
- **Description:** eval()
- **Evidence (Line):** `data.append(literal_eval("{2.3j, 1 - 2.3j, ()}"))`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 96. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/networkx/tests/test_lazy_imports.py:83
- **Description:** exec()
- **Evidence (Line):** `exec(s, {}, locls)`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 97. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/networkx/utils/decorators.py:916
- **Description:** exec()
- **Evidence (Line):** `exec(compiled, globl, locl)`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 98. [Critical] Insecure Deserialization
- **File:** .venv-test/lib/python3.12/site-packages/networkx/utils/tests/test_backends.py:28
- **Description:** pickle load/dumps
- **Evidence (Line):** `assert pickle.loads(pickled) is func.__wrapped__`
- **Exploit Scenario:** Attacker could achieve remote code execution
- **Fix Recommendation:** Use safe serialization formats (JSON), avoid pickle/yaml.load with untrusted data
- **Confidence:** High

### 99. [Critical] Insecure Deserialization
- **File:** .venv-test/lib/python3.12/site-packages/networkx/utils/tests/test_backends.py:34
- **Description:** pickle load/dumps
- **Evidence (Line):** `assert pickle.loads(pickled) is func`
- **Exploit Scenario:** Attacker could achieve remote code execution
- **Fix Recommendation:** Use safe serialization formats (JSON), avoid pickle/yaml.load with untrusted data
- **Confidence:** High

### 100. [Critical] Insecure Deserialization
- **File:** .venv-test/lib/python3.12/site-packages/networkx/utils/tests/test_backends.py:37
- **Description:** pickle load/dumps
- **Evidence (Line):** `assert pickle.loads(pickle.dumps(nx.inverse_line_graph)) is nx.inverse_line_graph`
- **Exploit Scenario:** Attacker could achieve remote code execution
- **Fix Recommendation:** Use safe serialization formats (JSON), avoid pickle/yaml.load with untrusted data
- **Confidence:** High

### 101. [Critical] Insecure Deserialization
- **File:** .venv-test/lib/python3.12/site-packages/networkx/utils/tests/test_config.py:47
- **Description:** pickle load/dumps
- **Evidence (Line):** `cfg2 = pickle.loads(pickle.dumps(cfg))`
- **Exploit Scenario:** Attacker could achieve remote code execution
- **Fix Recommendation:** Use safe serialization formats (JSON), avoid pickle/yaml.load with untrusted data
- **Confidence:** High

### 102. [Critical] Insecure Deserialization
- **File:** .venv-test/lib/python3.12/site-packages/networkx/utils/tests/test_config.py:102
- **Description:** pickle load/dumps
- **Evidence (Line):** `cfg2 = pickle.loads(pickle.dumps(cfg))`
- **Exploit Scenario:** Attacker could achieve remote code execution
- **Fix Recommendation:** Use safe serialization formats (JSON), avoid pickle/yaml.load with untrusted data
- **Confidence:** High

### 103. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/packaging/_parser.py:397
- **Description:** eval()
- **Evidence (Line):** `value = ast.literal_eval(python_str)`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 104. [Critical] Insecure Deserialization
- **File:** .venv-test/lib/python3.12/site-packages/packaging/_structures.py:10
- **Description:** pickle load/dumps
- **Evidence (Line):** `stand-in classes so that ``pickle.loads()`` can resolve those references.`
- **Exploit Scenario:** Attacker could achieve remote code execution
- **Fix Recommendation:** Use safe serialization formats (JSON), avoid pickle/yaml.load with untrusted data
- **Confidence:** High

### 105. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/pip/_internal/commands/configuration.py:248
- **Description:** subprocess with shell=True
- **Evidence (Line):** `subprocess.check_call(f'{editor} "{fname}"', shell=True)`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 106. [Critical] Hardcoded Secret
- **File:** .venv-test/lib/python3.12/site-packages/pip/_internal/network/auth.py:486
- **Description:** Password Assignment detected
- **Evidence (Line):** `password = ask_password("Password: ")`
- **Exploit Scenario:** Attacker could extract credentials and gain unauthorized access
- **Fix Recommendation:** Move secrets to environment variables or secret manager, rotate compromised credentials
- **Confidence:** High

### 107. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/pip/_vendor/distlib/scripts.py:165
- **Description:** exec()
- **Evidence (Line):** `# shebang, or else using os.exec() to run the entry script will`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 108. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/pip/_vendor/packaging/_parser.py:372
- **Description:** eval()
- **Evidence (Line):** `value = ast.literal_eval(python_str)`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 109. [Critical] Insecure Deserialization
- **File:** .venv-test/lib/python3.12/site-packages/pip/_vendor/packaging/_structures.py:10
- **Description:** pickle load/dumps
- **Evidence (Line):** `stand-in classes so that ``pickle.loads()`` can resolve those references.`
- **Exploit Scenario:** Attacker could achieve remote code execution
- **Fix Recommendation:** Use safe serialization formats (JSON), avoid pickle/yaml.load with untrusted data
- **Confidence:** High

### 110. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/pip/_vendor/pkg_resources/__init__.py:1714
- **Description:** exec()
- **Evidence (Line):** `exec(code, namespace, namespace)`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 111. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/pip/_vendor/pkg_resources/__init__.py:1725
- **Description:** exec()
- **Evidence (Line):** `exec(script_code, namespace, namespace)`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 112. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/pip/_vendor/pygments/formatters/__init__.py:91
- **Description:** eval()
- **Evidence (Line):** `this method is equivalent to running ``eval()`` on the input file. The formatter is`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 113. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/pip/_vendor/pygments/formatters/__init__.py:103
- **Description:** exec()
- **Evidence (Line):** `exec(f.read(), custom_namespace)`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 114. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/pip/_vendor/pygments/lexers/__init__.py:154
- **Description:** exec()
- **Evidence (Line):** `exec(f.read(), custom_namespace)`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 115. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/pip/_vendor/rich/markup.py:190
- **Description:** eval()
- **Evidence (Line):** `meta_params = literal_eval(parameters)`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 116. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/pluggy/_hooks.py:512
- **Description:** exec()
- **Evidence (Line):** `return self._hookexec(self.name, self._hookimpls.copy(), kwargs, firstresult)`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 117. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/pluggy/_hooks.py:534
- **Description:** exec()
- **Evidence (Line):** `res = self._hookexec(self.name, self._hookimpls.copy(), kwargs, False)`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 118. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/pluggy/_hooks.py:573
- **Description:** exec()
- **Evidence (Line):** `return self._hookexec(self.name, hookimpls, kwargs, firstresult)`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 119. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/pluggy/_hooks.py:580
- **Description:** exec()
- **Evidence (Line):** `res = self._hookexec(self.name, [method], kwargs, False)`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 120. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/pluggy/_manager.py:111
- **Description:** exec()
- **Evidence (Line):** `def _hookexec(`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 121. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/pluggy/_manager.py:120
- **Description:** exec()
- **Evidence (Line):** `return self._inner_hookexec(hook_name, methods, kwargs, firstresult)`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 122. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/pluggy/_manager.py:464
- **Description:** exec()
- **Evidence (Line):** `def traced_hookexec(`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 123. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/pydantic/_internal/_decorators.py:599
- **Description:** eval()
- **Evidence (Line):** `sig = signature_no_eval(validator)`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 124. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/pydantic/_internal/_decorators.py:637
- **Description:** eval()
- **Evidence (Line):** `sig = signature_no_eval(serializer)`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 125. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/pydantic/_internal/_decorators.py:675
- **Description:** eval()
- **Evidence (Line):** `sig = signature_no_eval(serializer)`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 126. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/pydantic/_internal/_decorators.py:707
- **Description:** eval()
- **Evidence (Line):** `sig = signature_no_eval(serializer)`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 127. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/pydantic/_internal/_decorators.py:755
- **Description:** eval()
- **Evidence (Line):** `sig = signature_no_eval(unwrap_wrapped_function(function))`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 128. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/pydantic/_internal/_decorators.py:779
- **Description:** eval()
- **Evidence (Line):** `sig = signature_no_eval(unwrap_wrapped_function(function))`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 129. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/pydantic/_internal/_fields.py:849
- **Description:** eval()
- **Evidence (Line):** `sig = _typing_extra.signature_no_eval(default_factory)`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 130. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/pydantic/_internal/_generate_schema.py:2030
- **Description:** eval()
- **Evidence (Line):** `sig = _typing_extra.signature_no_eval(function)`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 131. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/pydantic/_internal/_generate_schema.py:2055
- **Description:** eval()
- **Evidence (Line):** `sig = _typing_extra.signature_no_eval(function)`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 132. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/pydantic/_internal/_generate_schema.py:2134
- **Description:** eval()
- **Evidence (Line):** `sig = _typing_extra.signature_no_eval(function)`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 133. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/pydantic/_internal/_namespace_utils.py:38
- **Description:** eval()
- **Evidence (Line):** `return eval(typ, *ns)`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 134. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/pydantic/_internal/_signature.py:96
- **Description:** eval()
- **Evidence (Line):** `present_params = signature_no_eval(init).parameters.values()`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 135. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/pydantic/_internal/_typing_extra.py:458
- **Description:** eval()
- **Evidence (Line):** `def signature_no_eval(f: Callable[..., Any]) -> Signature:`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 136. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/pydantic/_internal/_validate_call.py:107
- **Description:** eval()
- **Evidence (Line):** `signature = signature_no_eval(self.function)`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 137. [Critical] Insecure Deserialization
- **File:** .venv-test/lib/python3.12/site-packages/pydantic/deprecated/parse.py:55
- **Description:** pickle load/dumps
- **Evidence (Line):** `return pickle.loads(bb)`
- **Exploit Scenario:** Attacker could achieve remote code execution
- **Fix Recommendation:** Use safe serialization formats (JSON), avoid pickle/yaml.load with untrusted data
- **Confidence:** High

### 138. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/pydantic/json_schema.py:1836
- **Description:** eval()
- **Evidence (Line):** `if len(_typing_extra.signature_no_eval(json_schema_extra).parameters) > 1:`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 139. [Critical] Hardcoded Secret
- **File:** .venv-test/lib/python3.12/site-packages/pydantic/types.py:1835
- **Description:** Password Assignment detected
- **Evidence (Line):** `user = User(username='scolvin', password='password1')`
- **Exploit Scenario:** Attacker could extract credentials and gain unauthorized access
- **Fix Recommendation:** Move secrets to environment variables or secret manager, rotate compromised credentials
- **Confidence:** High

### 140. [Critical] Hardcoded Secret
- **File:** .venv-test/lib/python3.12/site-packages/pydantic/types.py:1862
- **Description:** Password Assignment detected
- **Evidence (Line):** `model = Model(password='IAmSensitive', password_bytes=b'IAmSensitiveBytes')`
- **Exploit Scenario:** Attacker could extract credentials and gain unauthorized access
- **Fix Recommendation:** Move secrets to environment variables or secret manager, rotate compromised credentials
- **Confidence:** High

### 141. [Critical] Insecure Deserialization
- **File:** .venv-test/lib/python3.12/site-packages/pydantic/v1/parse.py:42
- **Description:** pickle load/dumps
- **Evidence (Line):** `return pickle.loads(bb)`
- **Exploit Scenario:** Attacker could achieve remote code execution
- **Fix Recommendation:** Use safe serialization formats (JSON), avoid pickle/yaml.load with untrusted data
- **Confidence:** High

### 142. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/pydantic/v1/utils.py:195
- **Description:** eval()
- **Evidence (Line):** `eval('__IPYTHON__')`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 143. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/pydantic/validate_call_decorator.py:29
- **Description:** eval()
- **Evidence (Line):** `_typing_extra.signature_no_eval(cast(_generate_schema.ValidateCallSupportedTypes, function))`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 144. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/pygments/formatters/__init__.py:91
- **Description:** eval()
- **Evidence (Line):** `this method is equivalent to running ``eval()`` on the input file. The formatter is`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 145. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/pygments/formatters/__init__.py:103
- **Description:** exec()
- **Evidence (Line):** `exec(f.read(), custom_namespace)`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 146. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/pygments/lexers/__init__.py:154
- **Description:** exec()
- **Evidence (Line):** `exec(f.read(), custom_namespace)`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 147. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/pygments/lexers/_julia_builtins.py:150
- **Description:** eval()
- **Evidence (Line):** `v = eval(Symbol(compl.mod))`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 148. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/pygments/lexers/_julia_builtins.py:361
- **Description:** eval()
- **Evidence (Line):** `v = eval(Symbol(compl.mod))`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 149. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/pygments/lexers/special.py:115
- **Description:** eval()
- **Evidence (Line):** `val = ast.literal_eval(val)`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 150. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/rich/markup.py:190
- **Description:** eval()
- **Evidence (Line):** `meta_params = literal_eval(parameters)`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 151. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/typing_extensions.py:1591
- **Description:** eval()
- **Evidence (Line):** `(unless you are familiar with how eval() and exec() work).  The`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 152. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/typing_extensions.py:4167
- **Description:** eval()
- **Evidence (Line):** `# as a way of emulating annotation scopes when calling `eval()``
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 153. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/typing_extensions.py:4172
- **Description:** eval()
- **Evidence (Line):** `value if not isinstance(value, str) else eval(value, globals, locals)`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 154. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/typing_extensions.py:4219
- **Description:** eval()
- **Evidence (Line):** `# If we pass None to eval() below, the globals of this module are used.`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 155. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/typing_extensions.py:4231
- **Description:** eval()
- **Evidence (Line):** `# as a way of emulating annotation scopes when calling `eval()``
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 156. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/typing_extensions.py:4254
- **Description:** eval()
- **Evidence (Line):** `value = eval(code, globals, locals)`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 157. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/typing_extensions.py:1591
- **Description:** exec()
- **Evidence (Line):** `(unless you are familiar with how eval() and exec() work).  The`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 158. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/typing_inspection/typing_objects.py:112
- **Description:** exec()
- **Evidence (Line):** `exec(func_code, globals_, locals_)`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 159. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/typing_inspection/typing_objects.py:153
- **Description:** exec()
- **Evidence (Line):** `exec(func_code, globals_, locals_)`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 160. [High] SQL Injection
- **File:** .venv-test/lib/python3.12/site-packages/mypy/metastore.py:216
- **Description:** SQL f-string interpolation
- **Evidence (Line):** `cur = db.execute(f"SELECT {field} FROM files2 WHERE path = ?", (name,))`
- **Exploit Scenario:** Attacker could manipulate SQL queries to access/modify/delete data
- **Fix Recommendation:** Use parameterized queries/prepared statements
- **Confidence:** Medium

### 161. [High] SQL Injection
- **File:** python/pydependencycheck/storage.py:370
- **Description:** SQL f-string interpolation
- **Evidence (Line):** `cursor.execute(f"DELETE FROM snapshots WHERE id IN ({placeholders})", old_ids)`
- **Exploit Scenario:** Attacker could manipulate SQL queries to access/modify/delete data
- **Fix Recommendation:** Use parameterized queries/prepared statements
- **Confidence:** Medium

### 162. [Medium] Weak Cryptography
- **File:** .venv-test/lib/python3.12/site-packages/coverage/lcovreport.py:43
- **Description:** MD5 usage
- **Evidence (Line):** `hashed = hashlib.md5(line.encode("utf-8"), usedforsecurity=False).digest()`
- **Exploit Scenario:** Weak algorithms vulnerable to collision/brute force attacks
- **Fix Recommendation:** Use modern algorithms (SHA-256+, bcrypt/argon2 for passwords, secrets module for tokens)
- **Confidence:** High

### 163. [Medium] Weak Cryptography
- **File:** .venv-test/lib/python3.12/site-packages/coverage/lcovreport.py:43
- **Description:** Weak hash algorithm
- **Evidence (Line):** `hashed = hashlib.md5(line.encode("utf-8"), usedforsecurity=False).digest()`
- **Exploit Scenario:** Weak algorithms vulnerable to collision/brute force attacks
- **Fix Recommendation:** Use modern algorithms (SHA-256+, bcrypt/argon2 for passwords, secrets module for tokens)
- **Confidence:** High

### 164. [Medium] Weak Cryptography
- **File:** .venv-test/lib/python3.12/site-packages/cryptography/hazmat/backends/openssl/backend.py:39
- **Description:** DES usage
- **Evidence (Line):** `# FIPS 140-3. To keep it simple we denylist any use of TripleDES (TDEA).`
- **Exploit Scenario:** Weak algorithms vulnerable to collision/brute force attacks
- **Fix Recommendation:** Use modern algorithms (SHA-256+, bcrypt/argon2 for passwords, secrets module for tokens)
- **Confidence:** High

### 165. [Medium] Weak Cryptography
- **File:** .venv-test/lib/python3.12/site-packages/cryptography/hazmat/decrepit/ciphers/algorithms.py:29
- **Description:** DES usage
- **Evidence (Line):** `class TripleDES(BlockCipherAlgorithm):`
- **Exploit Scenario:** Weak algorithms vulnerable to collision/brute force attacks
- **Fix Recommendation:** Use modern algorithms (SHA-256+, bcrypt/argon2 for passwords, secrets module for tokens)
- **Confidence:** High

### 166. [Medium] Weak Cryptography
- **File:** .venv-test/lib/python3.12/site-packages/cryptography/hazmat/decrepit/ciphers/algorithms.py:40
- **Description:** DES usage
- **Evidence (Line):** `"Single-key TripleDES (8-byte keys) is deprecated and "`
- **Exploit Scenario:** Weak algorithms vulnerable to collision/brute force attacks
- **Fix Recommendation:** Use modern algorithms (SHA-256+, bcrypt/argon2 for passwords, secrets module for tokens)
- **Confidence:** High

### 167. [Medium] Weak Cryptography
- **File:** .venv-test/lib/python3.12/site-packages/cryptography/hazmat/decrepit/ciphers/algorithms.py:49
- **Description:** DES usage
- **Evidence (Line):** `"Two-key TripleDES (16-byte keys) is deprecated and "`
- **Exploit Scenario:** Weak algorithms vulnerable to collision/brute force attacks
- **Fix Recommendation:** Use modern algorithms (SHA-256+, bcrypt/argon2 for passwords, secrets module for tokens)
- **Confidence:** High

### 168. [Medium] Weak Cryptography
- **File:** .venv-test/lib/python3.12/site-packages/cryptography/hazmat/decrepit/ciphers/algorithms.py:17
- **Description:** RC4 usage
- **Evidence (Line):** `class ARC4(CipherAlgorithm):`
- **Exploit Scenario:** Weak algorithms vulnerable to collision/brute force attacks
- **Fix Recommendation:** Use modern algorithms (SHA-256+, bcrypt/argon2 for passwords, secrets module for tokens)
- **Confidence:** High

### 169. [Medium] Weak Cryptography
- **File:** .venv-test/lib/python3.12/site-packages/cryptography/x509/extensions.py:72
- **Description:** SHA1 usage
- **Evidence (Line):** `return hashlib.sha1(data).digest()`
- **Exploit Scenario:** Weak algorithms vulnerable to collision/brute force attacks
- **Fix Recommendation:** Use modern algorithms (SHA-256+, bcrypt/argon2 for passwords, secrets module for tokens)
- **Confidence:** High

### 170. [Medium] Weak Cryptography
- **File:** .venv-test/lib/python3.12/site-packages/cryptography/x509/extensions.py:72
- **Description:** Weak hash algorithm
- **Evidence (Line):** `return hashlib.sha1(data).digest()`
- **Exploit Scenario:** Weak algorithms vulnerable to collision/brute force attacks
- **Fix Recommendation:** Use modern algorithms (SHA-256+, bcrypt/argon2 for passwords, secrets module for tokens)
- **Confidence:** High

### 171. [Medium] Weak Cryptography
- **File:** .venv-test/lib/python3.12/site-packages/gitdb/util.py:139
- **Description:** SHA1 usage
- **Evidence (Line):** `return hashlib.sha1(source)`
- **Exploit Scenario:** Weak algorithms vulnerable to collision/brute force attacks
- **Fix Recommendation:** Use modern algorithms (SHA-256+, bcrypt/argon2 for passwords, secrets module for tokens)
- **Confidence:** High

### 172. [Medium] Weak Cryptography
- **File:** .venv-test/lib/python3.12/site-packages/gitdb/util.py:139
- **Description:** Weak hash algorithm
- **Evidence (Line):** `return hashlib.sha1(source)`
- **Exploit Scenario:** Weak algorithms vulnerable to collision/brute force attacks
- **Fix Recommendation:** Use modern algorithms (SHA-256+, bcrypt/argon2 for passwords, secrets module for tokens)
- **Confidence:** High

### 173. [Medium] Weak Cryptography
- **File:** .venv-test/lib/python3.12/site-packages/google/protobuf/proto_builder.py:69
- **Description:** SHA1 usage
- **Evidence (Line):** `fields_hash = hashlib.sha1(usedforsecurity=False)`
- **Exploit Scenario:** Weak algorithms vulnerable to collision/brute force attacks
- **Fix Recommendation:** Use modern algorithms (SHA-256+, bcrypt/argon2 for passwords, secrets module for tokens)
- **Confidence:** High

### 174. [Medium] Weak Cryptography
- **File:** .venv-test/lib/python3.12/site-packages/google/protobuf/proto_builder.py:69
- **Description:** Weak hash algorithm
- **Evidence (Line):** `fields_hash = hashlib.sha1(usedforsecurity=False)`
- **Exploit Scenario:** Weak algorithms vulnerable to collision/brute force attacks
- **Fix Recommendation:** Use modern algorithms (SHA-256+, bcrypt/argon2 for passwords, secrets module for tokens)
- **Confidence:** High

### 175. [Medium] Weak Cryptography
- **File:** .venv-test/lib/python3.12/site-packages/jinja2/bccache.py:156
- **Description:** SHA1 usage
- **Evidence (Line):** `hash = sha1(name.encode("utf-8"))`
- **Exploit Scenario:** Weak algorithms vulnerable to collision/brute force attacks
- **Fix Recommendation:** Use modern algorithms (SHA-256+, bcrypt/argon2 for passwords, secrets module for tokens)
- **Confidence:** High

### 176. [Medium] Weak Cryptography
- **File:** .venv-test/lib/python3.12/site-packages/jinja2/bccache.py:165
- **Description:** SHA1 usage
- **Evidence (Line):** `return sha1(source.encode("utf-8")).hexdigest()`
- **Exploit Scenario:** Weak algorithms vulnerable to collision/brute force attacks
- **Fix Recommendation:** Use modern algorithms (SHA-256+, bcrypt/argon2 for passwords, secrets module for tokens)
- **Confidence:** High

### 177. [Medium] Weak Cryptography
- **File:** .venv-test/lib/python3.12/site-packages/jinja2/loaders.py:661
- **Description:** SHA1 usage
- **Evidence (Line):** `return "tmpl_" + sha1(name.encode("utf-8")).hexdigest()`
- **Exploit Scenario:** Weak algorithms vulnerable to collision/brute force attacks
- **Fix Recommendation:** Use modern algorithms (SHA-256+, bcrypt/argon2 for passwords, secrets module for tokens)
- **Confidence:** High

### 178. [Medium] Weak Cryptography
- **File:** .venv-test/lib/python3.12/site-packages/mypy/util.py:579
- **Description:** SHA1 usage
- **Evidence (Line):** `return hashlib.sha1(data).hexdigest()`
- **Exploit Scenario:** Weak algorithms vulnerable to collision/brute force attacks
- **Fix Recommendation:** Use modern algorithms (SHA-256+, bcrypt/argon2 for passwords, secrets module for tokens)
- **Confidence:** High

### 179. [Medium] Weak Cryptography
- **File:** .venv-test/lib/python3.12/site-packages/mypy/util.py:587
- **Description:** SHA1 usage
- **Evidence (Line):** `return hashlib.sha1(data).digest()`
- **Exploit Scenario:** Weak algorithms vulnerable to collision/brute force attacks
- **Fix Recommendation:** Use modern algorithms (SHA-256+, bcrypt/argon2 for passwords, secrets module for tokens)
- **Confidence:** High

### 180. [Medium] Weak Cryptography
- **File:** .venv-test/lib/python3.12/site-packages/mypy/util.py:579
- **Description:** Weak hash algorithm
- **Evidence (Line):** `return hashlib.sha1(data).hexdigest()`
- **Exploit Scenario:** Weak algorithms vulnerable to collision/brute force attacks
- **Fix Recommendation:** Use modern algorithms (SHA-256+, bcrypt/argon2 for passwords, secrets module for tokens)
- **Confidence:** High

### 181. [Medium] Weak Cryptography
- **File:** .venv-test/lib/python3.12/site-packages/mypy/util.py:587
- **Description:** Weak hash algorithm
- **Evidence (Line):** `return hashlib.sha1(data).digest()`
- **Exploit Scenario:** Weak algorithms vulnerable to collision/brute force attacks
- **Fix Recommendation:** Use modern algorithms (SHA-256+, bcrypt/argon2 for passwords, secrets module for tokens)
- **Confidence:** High

### 182. [Medium] Weak Cryptography
- **File:** .venv-test/lib/python3.12/site-packages/mypyc/build.py:302
- **Description:** SHA1 usage
- **Evidence (Line):** `h = hashlib.sha1()`
- **Exploit Scenario:** Weak algorithms vulnerable to collision/brute force attacks
- **Fix Recommendation:** Use modern algorithms (SHA-256+, bcrypt/argon2 for passwords, secrets module for tokens)
- **Confidence:** High

### 183. [Medium] Weak Cryptography
- **File:** .venv-test/lib/python3.12/site-packages/mypyc/build.py:302
- **Description:** Weak hash algorithm
- **Evidence (Line):** `h = hashlib.sha1()`
- **Exploit Scenario:** Weak algorithms vulnerable to collision/brute force attacks
- **Fix Recommendation:** Use modern algorithms (SHA-256+, bcrypt/argon2 for passwords, secrets module for tokens)
- **Confidence:** High

### 184. [Medium] Weak Cryptography
- **File:** .venv-test/lib/python3.12/site-packages/pip/_vendor/requests/auth.py:179
- **Description:** MD5 usage
- **Evidence (Line):** `return hashlib.md5(x, usedforsecurity=False).hexdigest()`
- **Exploit Scenario:** Weak algorithms vulnerable to collision/brute force attacks
- **Fix Recommendation:** Use modern algorithms (SHA-256+, bcrypt/argon2 for passwords, secrets module for tokens)
- **Confidence:** High

### 185. [Medium] Weak Cryptography
- **File:** .venv-test/lib/python3.12/site-packages/pip/_vendor/requests/auth.py:187
- **Description:** SHA1 usage
- **Evidence (Line):** `return hashlib.sha1(x, usedforsecurity=False).hexdigest()`
- **Exploit Scenario:** Weak algorithms vulnerable to collision/brute force attacks
- **Fix Recommendation:** Use modern algorithms (SHA-256+, bcrypt/argon2 for passwords, secrets module for tokens)
- **Confidence:** High

### 186. [Medium] Weak Cryptography
- **File:** .venv-test/lib/python3.12/site-packages/pip/_vendor/requests/auth.py:237
- **Description:** SHA1 usage
- **Evidence (Line):** `cnonce = hashlib.sha1(s, usedforsecurity=False).hexdigest()[:16]`
- **Exploit Scenario:** Weak algorithms vulnerable to collision/brute force attacks
- **Fix Recommendation:** Use modern algorithms (SHA-256+, bcrypt/argon2 for passwords, secrets module for tokens)
- **Confidence:** High

### 187. [Medium] Weak Cryptography
- **File:** .venv-test/lib/python3.12/site-packages/pip/_vendor/requests/auth.py:179
- **Description:** Weak hash algorithm
- **Evidence (Line):** `return hashlib.md5(x, usedforsecurity=False).hexdigest()`
- **Exploit Scenario:** Weak algorithms vulnerable to collision/brute force attacks
- **Fix Recommendation:** Use modern algorithms (SHA-256+, bcrypt/argon2 for passwords, secrets module for tokens)
- **Confidence:** High

### 188. [Medium] Weak Cryptography
- **File:** .venv-test/lib/python3.12/site-packages/pip/_vendor/requests/auth.py:187
- **Description:** Weak hash algorithm
- **Evidence (Line):** `return hashlib.sha1(x, usedforsecurity=False).hexdigest()`
- **Exploit Scenario:** Weak algorithms vulnerable to collision/brute force attacks
- **Fix Recommendation:** Use modern algorithms (SHA-256+, bcrypt/argon2 for passwords, secrets module for tokens)
- **Confidence:** High

### 189. [Medium] Weak Cryptography
- **File:** .venv-test/lib/python3.12/site-packages/pip/_vendor/requests/auth.py:237
- **Description:** Weak hash algorithm
- **Evidence (Line):** `cnonce = hashlib.sha1(s, usedforsecurity=False).hexdigest()[:16]`
- **Exploit Scenario:** Weak algorithms vulnerable to collision/brute force attacks
- **Fix Recommendation:** Use modern algorithms (SHA-256+, bcrypt/argon2 for passwords, secrets module for tokens)
- **Confidence:** High

### 190. [Medium] Weak Cryptography
- **File:** .venv-test/lib/python3.12/site-packages/pip/_vendor/rich/tree.py:18
- **Description:** DES usage
- **Evidence (Line):** `ASCII_GUIDES (GuideType): Guide lines used when Console.ascii_only is True.`
- **Exploit Scenario:** Weak algorithms vulnerable to collision/brute force attacks
- **Fix Recommendation:** Use modern algorithms (SHA-256+, bcrypt/argon2 for passwords, secrets module for tokens)
- **Confidence:** High

### 191. [Medium] Weak Cryptography
- **File:** .venv-test/lib/python3.12/site-packages/pip/_vendor/rich/tree.py:19
- **Description:** DES usage
- **Evidence (Line):** `TREE_GUIDES (List[GuideType, GuideType, GuideType]): Default guide lines.`
- **Exploit Scenario:** Weak algorithms vulnerable to collision/brute force attacks
- **Fix Recommendation:** Use modern algorithms (SHA-256+, bcrypt/argon2 for passwords, secrets module for tokens)
- **Confidence:** High

### 192. [Medium] Weak Cryptography
- **File:** .venv-test/lib/python3.12/site-packages/requests/auth.py:179
- **Description:** MD5 usage
- **Evidence (Line):** `return hashlib.md5(x, usedforsecurity=False).hexdigest()`
- **Exploit Scenario:** Weak algorithms vulnerable to collision/brute force attacks
- **Fix Recommendation:** Use modern algorithms (SHA-256+, bcrypt/argon2 for passwords, secrets module for tokens)
- **Confidence:** High

### 193. [Medium] Weak Cryptography
- **File:** .venv-test/lib/python3.12/site-packages/requests/auth.py:187
- **Description:** SHA1 usage
- **Evidence (Line):** `return hashlib.sha1(x, usedforsecurity=False).hexdigest()`
- **Exploit Scenario:** Weak algorithms vulnerable to collision/brute force attacks
- **Fix Recommendation:** Use modern algorithms (SHA-256+, bcrypt/argon2 for passwords, secrets module for tokens)
- **Confidence:** High

### 194. [Medium] Weak Cryptography
- **File:** .venv-test/lib/python3.12/site-packages/requests/auth.py:237
- **Description:** SHA1 usage
- **Evidence (Line):** `cnonce = hashlib.sha1(s, usedforsecurity=False).hexdigest()[:16]`
- **Exploit Scenario:** Weak algorithms vulnerable to collision/brute force attacks
- **Fix Recommendation:** Use modern algorithms (SHA-256+, bcrypt/argon2 for passwords, secrets module for tokens)
- **Confidence:** High

### 195. [Medium] Weak Cryptography
- **File:** .venv-test/lib/python3.12/site-packages/requests/auth.py:179
- **Description:** Weak hash algorithm
- **Evidence (Line):** `return hashlib.md5(x, usedforsecurity=False).hexdigest()`
- **Exploit Scenario:** Weak algorithms vulnerable to collision/brute force attacks
- **Fix Recommendation:** Use modern algorithms (SHA-256+, bcrypt/argon2 for passwords, secrets module for tokens)
- **Confidence:** High

### 196. [Medium] Weak Cryptography
- **File:** .venv-test/lib/python3.12/site-packages/requests/auth.py:187
- **Description:** Weak hash algorithm
- **Evidence (Line):** `return hashlib.sha1(x, usedforsecurity=False).hexdigest()`
- **Exploit Scenario:** Weak algorithms vulnerable to collision/brute force attacks
- **Fix Recommendation:** Use modern algorithms (SHA-256+, bcrypt/argon2 for passwords, secrets module for tokens)
- **Confidence:** High

### 197. [Medium] Weak Cryptography
- **File:** .venv-test/lib/python3.12/site-packages/requests/auth.py:237
- **Description:** Weak hash algorithm
- **Evidence (Line):** `cnonce = hashlib.sha1(s, usedforsecurity=False).hexdigest()[:16]`
- **Exploit Scenario:** Weak algorithms vulnerable to collision/brute force attacks
- **Fix Recommendation:** Use modern algorithms (SHA-256+, bcrypt/argon2 for passwords, secrets module for tokens)
- **Confidence:** High

### 198. [Medium] Weak Cryptography
- **File:** .venv-test/lib/python3.12/site-packages/rich/tree.py:18
- **Description:** DES usage
- **Evidence (Line):** `ASCII_GUIDES (GuideType): Guide lines used when Console.ascii_only is True.`
- **Exploit Scenario:** Weak algorithms vulnerable to collision/brute force attacks
- **Fix Recommendation:** Use modern algorithms (SHA-256+, bcrypt/argon2 for passwords, secrets module for tokens)
- **Confidence:** High

### 199. [Medium] Weak Cryptography
- **File:** .venv-test/lib/python3.12/site-packages/rich/tree.py:19
- **Description:** DES usage
- **Evidence (Line):** `TREE_GUIDES (List[GuideType, GuideType, GuideType]): Default guide lines.`
- **Exploit Scenario:** Weak algorithms vulnerable to collision/brute force attacks
- **Fix Recommendation:** Use modern algorithms (SHA-256+, bcrypt/argon2 for passwords, secrets module for tokens)
- **Confidence:** High
