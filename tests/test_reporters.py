"""Tests for report generators, including the HTML XSS fix.

`HtmlReporter` renders dependency metadata (package names, versions,
sources) that ultimately originates from third-party, untrusted sources:
a project's requirements.txt/pyproject.toml can declare (or a compromised
upstream index could serve) a "package name" containing arbitrary HTML/JS.
Before the fix, `HtmlReporter.generate()` interpolated these values into
the HTML report via an f-string with no escaping, so a malicious package
name like `<script>alert(1)</script>` would be rendered verbatim as an
executable <script> tag in anyone's browser when they opened the report
(a classic stored XSS).
"""

import json

from pydependencycheck.reporters import (
    CycloneDxReporter,
    HtmlReporter,
    JsonReporter,
    MarkdownReporter,
    escape,
)


class TestEscapeHelper:
    def test_escapes_script_tags(self):
        assert escape("<script>alert(1)</script>") == "&lt;script&gt;alert(1)&lt;/script&gt;"

    def test_escapes_quotes_used_for_attribute_breakout(self):
        payload = '" onmouseover="alert(1)'
        result = escape(payload)
        assert '"' not in result
        assert "&quot;" in result

    def test_none_becomes_empty_string(self):
        assert escape(None) == ""

    def test_passes_through_safe_text(self):
        assert escape("requests") == "requests"


class TestHtmlReporterXSS:
    """Prove malicious package manifest data cannot inject markup/script."""

    MALICIOUS_NAME = "<script>alert('xss')</script>"
    MALICIOUS_VERSION = '1.0"><img src=x onerror=alert(2)>'
    MALICIOUS_SOURCE = "requirements.txt<svg/onload=alert(3)>"

    def _malicious_deps(self):
        return [
            {
                "name": self.MALICIOUS_NAME,
                "version": self.MALICIOUS_VERSION,
                "direct": True,
                "source": self.MALICIOUS_SOURCE,
            }
        ]

    def test_malicious_package_name_is_neutralized(self):
        html_out = HtmlReporter().generate(self._malicious_deps())

        # The raw, unescaped payload must never appear in the output --
        # that's the actual injection vector.
        assert self.MALICIOUS_NAME not in html_out
        assert "<script>alert" not in html_out

        # The escaped form should be present instead, proving the data
        # made it into the report (just safely).
        assert "&lt;script&gt;" in html_out

    def test_malicious_version_cannot_break_out_of_attribute(self):
        html_out = HtmlReporter().generate(self._malicious_deps())
        assert "<img src=x onerror=" not in html_out

    def test_malicious_source_cannot_inject_svg_handler(self):
        html_out = HtmlReporter().generate(self._malicious_deps())
        assert "<svg/onload=" not in html_out

    def test_output_is_still_well_formed_around_escaped_payload(self):
        html_out = HtmlReporter().generate(self._malicious_deps())
        # The surrounding table structure should still be intact.
        assert "<table>" in html_out
        assert "</table>" in html_out
        assert "<strong>" in html_out

    def test_benign_dependency_still_renders_normally(self):
        html_out = HtmlReporter().generate(
            [{"name": "requests", "version": "2.32.0", "direct": True, "source": "requirements.txt"}]
        )
        assert "<strong>requests</strong>" in html_out
        assert "2.32.0" in html_out

    def test_ampersand_in_metadata_is_escaped(self):
        # Not an XSS vector by itself, but unescaped "&" produces invalid
        # HTML entities and is part of the same untrusted-data problem.
        html_out = HtmlReporter().generate(
            [{"name": "foo&bar", "version": "1.0", "direct": True, "source": "requirements.txt"}]
        )
        assert "foo&bar" not in html_out
        assert "foo&amp;bar" in html_out


class TestHtmlReporterBasics:
    def test_summary_counts(self):
        deps = [
            {"name": "a", "direct": True, "version": "1.0", "source": "requirements.txt"},
            {"name": "b", "direct": False, "version": "2.0", "source": "requirements.txt"},
        ]
        html_out = HtmlReporter().generate(deps)
        assert '<div class="stat-number">2</div>' in html_out

    def test_empty_dependencies_produces_valid_shell(self):
        html_out = HtmlReporter().generate([])
        assert "<!DOCTYPE html>" in html_out
        assert "</html>" in html_out


class TestJsonReporter:
    def test_generates_valid_json_with_summary(self):
        deps = [
            {"name": "requests", "version": "2.32.0", "direct": True},
            {"name": "urllib3", "version": "2.0.0", "direct": False},
        ]
        out = JsonReporter().generate(deps)
        data = json.loads(out)
        assert data["summary"]["total"] == 2
        assert data["summary"]["direct"] == 1
        assert data["summary"]["transitive"] == 1
        assert data["dependencies"] == deps


class TestMarkdownReporter:
    def test_generates_table_rows(self):
        deps = [{"name": "requests", "version": "2.32.0", "direct": True, "source": "requirements.txt"}]
        out = MarkdownReporter().generate(deps)
        assert "| `requests` | 2.32.0 | Direct | requirements.txt |" in out

    def test_does_not_html_escape_markdown_output(self):
        # Markdown output isn't rendered as HTML by this tool, so it's out
        # of scope for the XSS fix -- documented here so a future change
        # in how the markdown report gets displayed doesn't silently
        # reopen the same class of bug without anyone noticing.
        deps = [{"name": "<b>x</b>", "version": "1.0", "direct": True, "source": "requirements.txt"}]
        out = MarkdownReporter().generate(deps)
        assert "<b>x</b>" in out


class TestCycloneDxReporter:
    def test_generates_valid_cyclonedx_json(self):
        deps = [{"name": "requests", "version": "2.32.0"}]
        out = CycloneDxReporter().generate(deps)
        data = json.loads(out)
        assert data["bomFormat"] == "CycloneDX"
        assert data["components"][0]["purl"] == "pkg:pypi/requests@2.32.0"
