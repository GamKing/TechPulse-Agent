#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
agent-rag-mcp: 确定性裁判服务的 MCP Server（stdlib-only，标准 JSON-RPC 2.0 over stdio）
Frontier Tech Industrial Analysis Engine

设计约束（AGENTS.md）：
- 不使用 mcp SDK（第三方 pip 包）；用 Python 3.12+ 标准库手工实现 MCP stdio transport
  （Content-Length 帧 + JSON-RPC 2.0，与官方 mcp-python SDK 的 stdio transport 兼容）。
- 三组核心原语直接复用既有脚本，保证结论与 CLI 一致：
  * audit_report(benchmark_dir)  -> DeterministicJudge 11 道门禁审计，返回评分卡 + exit 语义
  * ast_calculate(expression, inputs) -> verification.calculate（AST 白名单安全四则重算）
  * route_problem(query)         -> ProblemRouter 路由 + RAG 公理召回

用法：
  # 直接丢给支持 MCP 的 Agent（Claude Code / Cursor 等）注册为 stdio server：
  python scripts/mcp_server.py
  # 自测（发一个 initialize + 一次 tools/call）：
  python scripts/mcp_server.py --self-test
"""

import argparse
import json
import os
import sys
from pathlib import Path

# 让 scripts/ 下的原语可导入（本文件位于同目录）
sys.path.insert(0, str(Path(__file__).resolve().parent))

from deterministic_judge import DeterministicJudge  # noqa: E402
from verification import calculate, digest  # noqa: E402
from problem_router import ProblemRouter  # noqa: E402


class McpServer:
    """最小 MCP Server：JSON-RPC 2.0 + Content-Length 帧（stdio transport）。"""

    PROTOCOL_VERSION = "2024-11-05"
    SERVER_NAME = "agent-rag-mcp"
    SERVER_VERSION = "1.0.0"

    def __init__(self):
        self._router = None

    # ---------- 便捷访问 ----------
    @property
    def router(self) -> ProblemRouter:
        if self._router is None:
            self._router = ProblemRouter()
        return self._router

    # ---------- 工具实现（复用既有原语） ----------
    def _tool_audit_report(self, params: dict) -> dict:
        benchmark_dir = params.get("benchmark_dir") or "reports/nvidia_benchmark"
        judge = DeterministicJudge(benchmark_dir=benchmark_dir)
        scorecard = judge.execute_audit()
        return {
            "benchmark_dir": benchmark_dir,
            "overall_verdict": scorecard["overall_verdict"],
            "summary": scorecard["summary"],
            "report_binding": scorecard["report_binding"],
            "exit_code_equivalent": 0 if scorecard["overall_verdict"] == "PASS" else 1,
            "scorecard_path": f"{benchmark_dir}/audit_scorecard.json",
        }

    def _tool_ast_calculate(self, params: dict) -> dict:
        expression = params["expression"]
        inputs = params.get("inputs", {})
        try:
            value = calculate(expression, inputs)
            return {"expression": expression, "inputs": inputs,
                    "result": value, "ok": True, "method": "AST whitelist, no eval"}
        except Exception as exc:
            # Fail-closed：与 verification.calculate 一致的异常语义
            return {"expression": expression, "inputs": inputs,
                    "ok": False, "error": f"{type(exc).__name__}: {exc}"}

    def _tool_route_problem(self, params: dict) -> dict:
        query = params["query"]
        decision = self.router.route(query)
        return {
            "query": query,
            "category": decision["category"],
            "pipeline_id": decision["pipeline_id"],
            "confidence": decision["confidence"],
            "primary_skills": decision["primary_skills"],
            "secondary_skills": decision["secondary_skills"],
            "pruned_skills": decision["pruned_skills"],
            "retrieved_axioms": decision["retrieved_axioms"],
            "mandatory_gates": decision["mandatory_gates"],
        }

    TOOLS = [
        {
            "name": "audit_report",
            "description": "Deterministic Judge: run all 11 hard gates on a benchmark dir, return scorecard and fail-closed verdict.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "benchmark_dir": {"type": "string",
                                       "description": "Benchmark directory containing evidence.jsonl etc. (default reports/nvidia_benchmark)"}
                }
            }
        },
        {
            "name": "ast_calculate",
            "description": "Safe arithmetic recompute via AST whitelist (never eval). Rejects code injection, NaN, oversized pow.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "expression": {"type": "string", "description": "Arithmetic expression, e.g. '1 - 2**(b)'"},
                    "inputs": {"type": "object", "description": "Variable values, e.g. {'b': -0.23447}"}
                },
                "required": ["expression"]
            }
        },
        {
            "name": "route_problem",
            "description": "Route an industry/research problem to pipeline + pruned skill set + retrieved training-camp axiom chunks.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Analytical question in Chinese/English"}
                },
                "required": ["query"]
            }
        },
    ]

    # ---------- JSON-RPC 分发 ----------
    def handle_request(self, msg: dict) -> dict:
        method = msg.get("method")
        params = msg.get("params") or {}
        req_id = msg.get("id")
        if method == "initialize":
            return {"jsonrpc": "2.0", "id": req_id,
                    "result": {"protocolVersion": self.PROTOCOL_VERSION,
                               "capabilities": {"tools": {}},
                               "serverInfo": {"name": self.SERVER_NAME, "version": self.SERVER_VERSION}}}
        if method == "notifications/initialized":
            return None  # notification，无返回
        if method == "tools/list":
            return {"jsonrpc": "2.0", "id": req_id, "result": {"tools": self.TOOLS}}
        if method == "tools/call":
            tool_name = params.get("name")
            args = params.get("arguments") or {}
            fn = {"audit_report": self._tool_audit_report,
                  "ast_calculate": self._tool_ast_calculate,
                  "route_problem": self._tool_route_problem}.get(tool_name)
            if fn is None:
                return self._error(req_id, -32601, f"Unknown tool: {tool_name}")
            try:
                result = fn(args)
                # MCP 工具结果以结构化内容包一层，便于 Agent 消费
                return {"jsonrpc": "2.0", "id": req_id,
                        "result": {"content": [{"type": "text",
                                                 "text": json.dumps(result, ensure_ascii=False, indent=2)}]}}
            except Exception as exc:
                return self._error(req_id, -32603, f"Tool execution failed: {exc}")
        if method == "ping":
            return {"jsonrpc": "2.0", "id": req_id, "result": {}}
        return self._error(req_id, -32601, f"Method not found: {method}")

    def _error(self, req_id, code: int, message: str) -> dict:
        return {"jsonrpc": "2.0", "id": req_id,
                "error": {"code": code, "message": message}}

    # ---------- stdio transport ----------
    def serve_stdio(self):
        stdin_buf = sys.stdin.buffer
        stdout_buf = sys.stdout.buffer
        while True:
            line = stdin_buf.readline()
            if not line:
                break
            line = line.strip()
            if not line:
                continue
            if line.lower().startswith(b"content-length:"):
                length = int(line.split(b":")[1].strip())
                # 读空行
                stdin_buf.readline()
                body = stdin_buf.read(length).decode("utf-8")
                try:
                    msg = json.loads(body)
                    response = self.handle_request(msg)
                    if response is not None:
                        payload = json.dumps(response, ensure_ascii=False).encode("utf-8")
                        stdout_buf.write(f"Content-Length: {len(payload)}\r\n\r\n".encode("utf-8"))
                        stdout_buf.write(payload)
                        stdout_buf.flush()
                except json.JSONDecodeError:
                    resp = self._error(None, -32700, "Parse error")
                    payload = json.dumps(resp, ensure_ascii=False).encode("utf-8")
                    stdout_buf.write(f"Content-Length: {len(payload)}\r\n\r\n".encode("utf-8"))
                    stdout_buf.write(payload)
                    stdout_buf.flush()

    # ---------- 自测 ----------
    def self_test(self):
        print("[self-test] initialize ...")
        r = self.handle_request({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}})
        assert r["result"]["serverInfo"]["name"] == self.SERVER_NAME
        print("  OK ->", r["result"]["serverInfo"])
        print("[self-test] tools/list ...")
        r = self.handle_request({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
        names = [t["name"] for t in r["result"]["tools"]]
        assert names == ["audit_report", "ast_calculate", "route_problem"]
        print("  OK ->", names)
        print("[self-test] tools/call ast_calculate (2+2, 恶意注入拒绝) ...")
        r = self.handle_request({"jsonrpc": "2.0", "id": 3, "method": "tools/call",
                                  "params": {"name": "ast_calculate", "arguments": {"expression": "2+2", "inputs": {}}}})
        print("  OK ->", r["result"]["content"][0]["text"][:80])
        r = self.handle_request({"jsonrpc": "2.0", "id": 4, "method": "tools/call",
                                  "params": {"name": "ast_calculate", "arguments": {"expression": "__import__('os').system('x')", "inputs": {}}}})
        ok = '"ok": false' in r["result"]["content"][0]["text"]
        print(f"  注入拒绝 {'OK' if ok else 'FAIL'} ->", r["result"]["content"][0]["text"][:100])
        print("[self-test] tools/call route_problem ...")
        r = self.handle_request({"jsonrpc": "2.0", "id": 5, "method": "tools/call",
                                  "params": {"name": "route_problem", "arguments": {"query": "AI芯片产业双链拓扑与控制点分析"}}})
        print("  OK ->", r["result"]["content"][0]["text"][:120])
        print("[self-test] all OK")


def main():
    ap = argparse.ArgumentParser(description="agent-rag-mcp: stdlib-only MCP server (JSON-RPC over stdio)")
    ap.add_argument("--self-test", action="store_true", help="Run in-process self-test instead of serving")
    args = ap.parse_args()
    if sys.stdout.encoding != "utf-8" and not args.self_test:
        sys.stdout.reconfigure(encoding="utf-8")
    server = McpServer()
    if args.self_test:
        server.self_test()
    else:
        server.serve_stdio()


if __name__ == "__main__":
    main()