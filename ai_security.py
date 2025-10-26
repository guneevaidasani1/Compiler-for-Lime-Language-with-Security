# ai_security_enhanced.py
import json
import re
from typing import Dict, List, Any, Optional
from pathlib import Path
from dataclasses import dataclass
from enum import Enum
import textwrap

class VulnerabilityType(Enum):
    BUFFER_OVERFLOW = "buffer_overflow"
    INJECTION = "injection" 
    INTEGER_OVERFLOW = "integer_overflow"
    UNINITIALIZED_MEMORY = "uninitialized_memory"
    FORMAT_STRING = "format_string"
    MEMORY_LEAK = "memory_leak"
    UNSAFE_FUNCTION = "unsafe_function"

@dataclass
class SecurityFinding:
    type: VulnerabilityType
    severity: str
    confidence: float
    location: str
    description: str
    explanation: str
    risk_impact: str
    fix_suggestion: str
    code_example: str
    cwe_id: str

class AdvancedSecurityAnalyzer:
    """
    Deterministic taint-analysis based security analyzer, augmented with LLM for explanations.
    """

    def __init__(self, min_confidence: float = 0.5):
        self.min_confidence = min_confidence
        #so these are our sinks , they are dangerous api calls or operation
        self.SINKS = {
            'FORMAT_STRING': {
                'functions': {'printf', 'sprintf', 'fprintf'},
                'cwe': 'CWE-134',
                'severity': 'HIGH',
                'type': VulnerabilityType.FORMAT_STRING,
                'description': 'Format String Vulnerability'
            },
            'INJECTION': {
                'functions': {'exec', 'system', 'eval', 'query'},
                'cwe': 'CWE-89',
                'severity': 'CRITICAL',
                'type': VulnerabilityType.INJECTION,
                'description': 'Command/Query Injection'
            }
        }
        ##this defines our untrustable input set
        self.TAINT_SOURCES_FUNCS = {'read_input', 'readline', 'gets'}
        self.SANITIZERS = {'sanitize', 'escape', 'encode'}

    def analyze_with_explanations(self, ast_file: str) -> Dict[str, Any]:
        """Run taint analysis and build report."""
        print("   Scanning for security vulnerabilities (deterministic taint analysis)...")
        try:
            with open(ast_file, 'r', encoding='utf-8') as f:
                ast_data = json.load(f)
            findings = self._taint_analysis(ast_data)
            # Confidence filtering
            findings = [f for f in findings if f.confidence >= self.min_confidence]
            return self._generate_comprehensive_report(findings)
        except Exception as e:
            print(f"   Security analysis error: {e}")
            return {'findings': [], 'summary': {'total_findings': 0, 'risk_level': 'LOW'}}

   
    def _taint_analysis(self, ast: Dict[str, Any]) -> List['SecurityFinding']:
        findings: List[SecurityFinding] = []

        def normalize(node):
            """Unwrap top-level Program statements like {'LetStatement': {...}} -> {...}.
            Leaves other nodes unchanged.
            """
            if isinstance(node, dict) and len(node) == 1:
                (k, v), = node.items()
                if isinstance(v, dict) and 'type' in v:
                    return v
            return node

        def is_node(n, t):
            n = normalize(n)
            return isinstance(n, dict) and n.get('type') == t

        def ident_name(n: Dict[str, Any]) -> Optional[str]:
            n = normalize(n)
            if not is_node(n, 'IdentifierLiteral'):
                return None
            return n.get('value')

        def eval_expr_taint(expr: Dict[str, Any], taint_map: Dict[str, bool]) -> bool:
            """Return True if TAINTED, False otherwise."""
            expr = normalize(expr)
            if not isinstance(expr, dict):
                return False
            t = expr.get('type')
            if t in ['IntegerLiteral', 'FloatLiteral', 'StringLiteral', 'BooleanLiteral']:
                return False
            if t == 'IdentifierLiteral':
                name = expr.get('value')
                return bool(taint_map.get(name, False))
            if t == 'InfixExpression':
                left = normalize(expr.get('left_node') or expr.get('left'))
                right = normalize(expr.get('right_node') or expr.get('right'))
                return eval_expr_taint(left, taint_map) or eval_expr_taint(right, taint_map) 
                #if anything is tained we return the full expression as tainted
            if t == 'CallExpression':
                fn = normalize(expr.get('function') or {})
                fname = fn.get('value') if isinstance(fn, dict) else None
                
                if fname in self.TAINT_SOURCES_FUNCS:
                    return True
                
                if fname in self.SANITIZERS:
                    return False
                
                for a in (expr.get('arguments', []) or []):
                    a = normalize(a)
                    if isinstance(a, dict) and eval_expr_taint(a, taint_map):
                        return True
                return False
            return False

        def render_expr(expr: Dict[str, Any]) -> str:
            try:
                return json.dumps(expr)
            except Exception:
                return str(expr)

        def check_sinks_in_expr(expr: Dict[str, Any], taint_map: Dict[str, bool], location_ctx: str):
            expr = normalize(expr)
            if not isinstance(expr, dict):
                return
            if expr.get('type') == 'CallExpression':
                fn = normalize(expr.get('function') or {})
                fname = fn.get('value') if isinstance(fn, dict) else None
                args = [normalize(a) for a in (expr.get('arguments', []) or [])]
                
                if fname in self.SINKS['FORMAT_STRING']['functions'] and args:
                    first = args[0]
                    is_const = isinstance(first, dict) and first.get('type') == 'StringLiteral'
                    if not is_const:
                        tainted = eval_expr_taint(first, taint_map)
                        sev = 'HIGH' if tainted else 'MEDIUM'
                        conf = 1.0 if tainted else 0.8
                        findings.append(self._llm_finding(
                            sink_key='FORMAT_STRING',
                            location=f"Call:{fname} at {location_ctx}",
                            snippet=render_expr(expr),
                            severity_override=sev,
                            confidence_override=conf
                        ))
                
                if fname in self.SINKS['INJECTION']['functions']:
                    tainted = any(eval_expr_taint(a, taint_map) for a in args if isinstance(a, dict))
                    risky_concat = any(isinstance(a, dict) and a.get('type') == 'InfixExpression' and a.get('operator') == '+' for a in args)
                    if tainted or risky_concat:
                        sev = 'CRITICAL' if tainted else 'MEDIUM'
                        conf = 1.0 if tainted else 0.75
                        findings.append(self._llm_finding(
                            sink_key='INJECTION',
                            location=f"Call:{fname} at {location_ctx}",
                            snippet=render_expr(expr),
                            severity_override=sev,
                            confidence_override=conf
                        ))
           
            for k, v in list(expr.items()):
                if isinstance(v, dict):
                    check_sinks_in_expr(v, taint_map, location_ctx)
                elif isinstance(v, list):
                    for it in v:
                        if isinstance(it, dict):
                            check_sinks_in_expr(it, taint_map, location_ctx)

        def analyze_block(block: Dict[str, Any], taint_map: Dict[str, bool], func_ctx: str):
            if not isinstance(block, dict):
                return taint_map
            for stmt in (block.get('statements', []) or []):
                stmt = normalize(stmt)
                t = stmt.get('type')
                if t == 'LetStatement':
                    name = ident_name(stmt.get('name'))
                    value = stmt.get('value')
                    tv = eval_expr_taint(value, taint_map)
                    
                    vtype = stmt.get('value_type')
                    if vtype == 'str':
                        
                        tv = tv or (value is None)
                    if name:
                        taint_map[name] = bool(tv)
                    check_sinks_in_expr(value, taint_map, func_ctx)
                elif t == 'AssignStatement':
                    name = ident_name(stmt.get('ident'))
                    rv = stmt.get('right_value')
                    tv = eval_expr_taint(rv, taint_map)
                    if name:
                        taint_map[name] = bool(tv)
                    check_sinks_in_expr(rv, taint_map, func_ctx)
                elif t == 'ExpressionStatement':
                    expr = stmt.get('expr')
                    check_sinks_in_expr(expr, taint_map, func_ctx)
                elif t == 'IfStatement':
                    
                    cons = stmt.get('consequence')
                    alt = stmt.get('alternative')
                    map_a = dict(taint_map)
                    map_b = dict(taint_map)
                    analyze_block(cons, map_a, func_ctx)
                    if alt:
                        analyze_block(alt, map_b, func_ctx)
                    
                    keys = set(map_a.keys()) | set(map_b.keys()) | set(taint_map.keys())
                    for k in keys:
                        taint_map[k] = bool(map_a.get(k, False) or map_b.get(k, False) or taint_map.get(k, False))
                elif t == 'WhileStatement' or t == 'ForStatement':
                    
                    cond = stmt.get('condition') or {}
                    def _has_large_int(n):
                        if isinstance(n, dict):
                            if n.get('type') == 'IntegerLiteral' and int(n.get('value', 0)) >= 100000:
                                return True
                            return any(_has_large_int(v) for v in n.values() if isinstance(v, (dict, list)))
                        if isinstance(n, list):
                            return any(_has_large_int(x) for x in n)
                        return False
                    if _has_large_int(cond):
                        findings.append(SecurityFinding(
                            type=VulnerabilityType.BUFFER_OVERFLOW,
                            severity='LOW',
                            confidence=0.6,
                            location=f"{t} at {func_ctx}",
                            description='Potential resource exhaustion loop',
                            explanation='A loop with a very large bound may lead to resource exhaustion in this toy environment.',
                            risk_impact='May cause long execution or denial of service in limited environments.',
                            fix_suggestion='Use reasonable bounds and add checks; for buffer operations perform explicit bounds checks.',
                            code_example='',
                            cwe_id='CWE-400'
                        ))
                    body = stmt.get('body')
                    
                    analyze_block(body, taint_map, func_ctx)
                elif t == 'ReturnStatement':
                    check_sinks_in_expr(stmt.get('return_value'), taint_map, func_ctx)
                elif t == 'ImportStatement':
                    pass
            return taint_map

        def analyze_function(fn_node: Dict[str, Any]):
            fname = ident_name(fn_node.get('name')) or '<anon>'
            params: List[Dict[str, Any]] = fn_node.get('parameters', []) or []
            taint_map: Dict[str, bool] = {}
            
            for p in params:
                if isinstance(p, dict):
                    pname = p.get('name')
                    ptype = p.get('value_type')
                    if pname:
                        taint_map[pname] = (ptype == 'str')
            body = fn_node.get('body')
            analyze_block(body, taint_map, f"fn {fname}")

        
        if ast.get('type') == 'Program':
            for s in (ast.get('statements', []) or []):
                s = normalize(s)
                if is_node(s, 'FunctionStatement'):
                    analyze_function(s)
                else:
                    
                    analyze_block({'statements': [s]}, {}, 'top-level')
        else:
            analyze_block(ast, {}, 'unknown')

        return self._deduplicate_findings(findings)

    

    def _llm_finding(self, sink_key: str, location: str, snippet: str, *, severity_override: Optional[str]=None, confidence_override: Optional[float]=None) -> 'SecurityFinding':
        meta = self.SINKS[sink_key]
        llm_json = self._query_gemini_for_json(sink_key, location, snippet)
        explanation = llm_json.get('explanation', f"Tainted data reaches {meta['description']}.")
        risk = llm_json.get('risk_impact', 'Exploitable if attacker controls the tainted input.')
        fix = llm_json.get('fix_suggestion', 'Use safe patterns and validate inputs. For printf, use constant format string; for commands/queries, use parameterization.')
        example = llm_json.get('code_example', '')
        return SecurityFinding(
            type=meta['type'],
            severity=severity_override or meta['severity'],
            confidence=confidence_override if confidence_override is not None else 1.0,
            location=location,
            description=meta['description'],
            explanation=explanation,
            risk_impact=risk,
            fix_suggestion=fix,
            code_example=example,
            cwe_id=meta['cwe']
        )

    def _query_gemini_for_json(self, sink_key: str, location: str, snippet: str) -> Dict[str, Any]:
        """Call Gemini to produce a structured JSON explanation. Falls back to defaults on failure."""
        import os
        import json as _json
        api_key = os.environ.get('AIzaSyD33KJwZj9CN2skx61N0cYDhz2Xa_VI6l0')
        if not api_key:
            return {}
        prompt = {
            'role': 'user',
            'parts': [{
                'text': (
                    "You are generating a security finding for a Lime language static analyzer.\n"
                    f"Sink type: {sink_key}. Location: {location}.\n"
                    "Provide a concise JSON with keys: explanation, risk_impact, fix_suggestion, code_example.\n"
                    "Explain why the taint flow is dangerous and give a secure rewrite.\n"
                    f"Code snippet (JSON AST fragment or text):\n{snippet}"
                )
            }]
        }
        body = _json.dumps({'contents': [prompt]})
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
        try:
            try:
                import requests
                r = requests.post(url, headers={'Content-Type': 'application/json'}, data=body, timeout=10)
                data = r.json()
            except Exception:
                
                from urllib import request as _r
                req = _r.Request(url, data=body.encode('utf-8'), headers={'Content-Type': 'application/json'})
                with _r.urlopen(req, timeout=10) as resp:
                    data = json.loads(resp.read().decode('utf-8'))
            
            cand = (data.get('candidates') or [{}])[0]
            parts = (cand.get('content') or {}).get('parts') or []
            text = ''.join([p.get('text', '') for p in parts])
           
            m = re.search(r"\{[\s\S]*\}", text)
            if m:
                return json.loads(m.group(0))
            return {}
        except Exception:
            return {}

    
    def _deep_ast_analysis(self, ast_data: Dict[str, Any]) -> List[SecurityFinding]:
        
        return []
    

    
    def _get_node_location(self, node: Dict[str, Any]) -> str:
    
        try:
            components = []
            if 'type' in node:
                components.append(node['type'])
            for key in ['name', 'function', 'ident']:
                if key in node:
                    if isinstance(node[key], dict) and 'value' in node[key]:
                        components.append(f"{key}:{node[key]['value']}")
            return " -> ".join(components) if components else "Unknown"
        except Exception:
            return 'Unknown'
    
    def _deduplicate_findings(self, findings: List[SecurityFinding]) -> List[SecurityFinding]:
        """Remove duplicate findings"""
        seen = set()
        unique = []
        
        for finding in findings:
            key = (finding.location, finding.type.value)
            if key not in seen:
                seen.add(key)
                unique.append(finding)
        
        
        severity_order = {'CRITICAL': 0, 'HIGH': 1, 'MEDIUM': 2, 'LOW': 3}
        unique.sort(key=lambda x: severity_order.get(x.severity, 4))
        
        return unique
    
    def _generate_comprehensive_report(self, findings: List[SecurityFinding]) -> Dict[str, Any]:
        """Generate detailed security report"""
        summary = {
            'total_findings': len(findings),
            'by_severity': {},
            'by_type': {},
            'risk_level': 'LOW'
        }
        
        for finding in findings:
            summary['by_severity'][finding.severity] = summary['by_severity'].get(finding.severity, 0) + 1
            summary['by_type'][finding.type.value] = summary['by_type'].get(finding.type.value, 0) + 1
        
    
        if summary['by_severity'].get('CRITICAL', 0) > 0:
            summary['risk_level'] = 'CRITICAL'
        elif summary['by_severity'].get('HIGH', 0) > 0:
            summary['risk_level'] = 'HIGH'
        elif summary['by_severity'].get('MEDIUM', 0) > 0:
            summary['risk_level'] = 'MEDIUM'
        
        return {
            'summary': summary,
            'findings': [self._finding_to_dict(f) for f in findings]
        }

    def export_report(self, report: Dict[str, Any], out_dir: str = "debug", basename: str = "security_report", formats: list[str] = None) -> list[str]:
        """Export security report to JSON/Markdown files and return file paths"""
        import os
        os.makedirs(out_dir, exist_ok=True)
        if formats is None:
            formats = ["json", "md"]
        paths: list[str] = []
        if "json" in formats:
            json_path = os.path.join(out_dir, f"{basename}.json")
            with open(json_path, 'w') as jf:
                json.dump(report, jf, indent=2)
            paths.append(json_path)
        if "md" in formats:
            md_path = os.path.join(out_dir, f"{basename}.md")
            with open(md_path, 'w') as mf:
                mf.write(self._report_to_markdown(report))
            paths.append(md_path)
        return paths

    def _report_to_markdown(self, report: Dict[str, Any]) -> str:
        summary = report.get('summary', {})
        findings = report.get('findings', [])
        lines = []
        lines.append("# AI Security Analysis Report")
        lines.append("")
        lines.append(f"- Total Findings: {summary.get('total_findings', len(findings))}")
        lines.append(f"- Risk Level: {summary.get('risk_level', 'LOW')}")
        lines.append("")
        if not findings:
            lines.append("No security vulnerabilities detected.")
            return "\n".join(lines)
        by_sev: dict[str, list[dict]] = {}
        for f in findings:
            by_sev.setdefault(f['severity'], []).append(f)
        for sev in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']:
            if sev in by_sev:
                lines.append(f"## {sev} Findings ({len(by_sev[sev])})")
                for i, f in enumerate(by_sev[sev], 1):
                    lines.append(f"### {i}. {f['description']}")
                    lines.append(f"- Location: {f['location']}")
                    lines.append(f"- Confidence: {f['confidence']}")
                    lines.append(f"- CWE: {f['cwe_id']}")
                    lines.append(f"- Explanation: {f['explanation']}")
                    lines.append(f"- Risk: {f['risk_impact']}")
                    lines.append(f"- Fix: {f['fix_suggestion']}")
                    lines.append("")
        return "\n".join(lines)
    
    def _finding_to_dict(self, finding: SecurityFinding) -> Dict[str, Any]:
        """Convert finding to dictionary"""
        return {
            'type': finding.type.value,
            'severity': finding.severity,
            'confidence': finding.confidence,
            'location': finding.location,
            'description': finding.description,
            'explanation': finding.explanation,
            'risk_impact': finding.risk_impact,
            'fix_suggestion': finding.fix_suggestion,
            'code_example': finding.code_example,
            'cwe_id': finding.cwe_id
        }
    
    def should_proceed(self, report: Dict[str, Any], security_level: str) -> bool:
        """Determine if compilation should proceed based on security level"""
        if security_level == 'permissive':
            return True
        
        findings = report.get('findings', [])
        
        if security_level == 'strict':
           
            critical_count = len([f for f in findings if f['severity'] in ['CRITICAL', 'HIGH']])
            if critical_count > 0:
                self._print_detailed_report(report)
                return False
        
        self._print_detailed_report(report)
        return True
    
    def _print_detailed_report(self, report: Dict[str, Any]):
        """Print comprehensive security report"""
        findings = report.get('findings', [])
        summary = report.get('summary', {})
        
        print(f"\n   AI SECURITY ASSESSMENT")
        print("   " + "=" * 50)
        print(f"   Total Findings: {summary.get('total_findings', 0)}")
        print(f"   Risk Level: {summary.get('risk_level', 'LOW')}")
        
        if not findings:
            print("   No security vulnerabilities detected!")
            return
        
       
        by_severity = {}
        for finding in findings:
            severity = finding['severity']
            if severity not in by_severity:
                by_severity[severity] = []
            by_severity[severity].append(finding)
        
        
        for severity in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']:
            if severity in by_severity:
                print(f"\n   {severity} SEVERITY:")
                print("   " + "-" * 40)
                
                for i, finding in enumerate(by_severity[severity], 1):
                    print(f"   {i}. {finding['description']}")
                    print(f"      Location: {finding['location']}")
                    print(f"      Explanation: {finding['explanation']}")
                    print(f"      Risk: {finding['risk_impact']}")
                    print(f"      Fix: {finding['fix_suggestion']}")
                    print(f"      CWE: {finding['cwe_id']}")
                    print(f"      Confidence: {finding['confidence']:.2f}")
                    print()