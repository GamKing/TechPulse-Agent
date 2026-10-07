"""Small, fail-closed verification primitives (standard library only)."""
import ast
import hashlib
import math
import operator
from html.parser import HTMLParser
from urllib.parse import urlsplit
from urllib.request import Request, urlopen


def digest(data):
    return 'sha256:' + hashlib.sha256(data).hexdigest()


class TextParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []
        self.hidden = 0

    def handle_starttag(self, tag, attrs):
        if tag in ('script', 'style'):
            self.hidden += 1

    def handle_endtag(self, tag):
        if tag in ('script', 'style'):
            self.hidden = max(0, self.hidden - 1)

    def handle_data(self, data):
        if not self.hidden:
            self.parts.append(data)


def fetch_source(url):
    if urlsplit(url).scheme not in ('http', 'https'):
        raise ValueError('Only HTTP(S) sources are supported')
    with urlopen(Request(url, headers={'User-Agent': 'EvidenceAuditor/1.0'}), timeout=20) as response:
        body = response.read(2_000_001)
        if len(body) > 2_000_000:
            raise ValueError('Source exceeds 2 MB limit; use a dedicated extractor')
        content_type = response.headers.get_content_type()
        if content_type not in ('text/html', 'text/plain'):
            raise ValueError('Unsupported source format: ' + content_type)
        text = body.decode(response.headers.get_content_charset() or 'utf-8', errors='strict')
        if content_type == 'text/html':
            parser = TextParser()
            parser.feed(text)
            text = ' '.join(parser.parts)
        return body, ' '.join(text.split()), response.status, response.geturl()


def _lookup_offline_manifest(benchmark_dir):
    """读取 source_snapshots/manual/manifest.json（离线凭证清单）。"""
    from pathlib import Path
    mf = Path(benchmark_dir) / "source_snapshots/manual/manifest.json"
    if not mf.is_file():
        return {}
    try:
        import json
        return json.loads(mf.read_text(encoding="utf-8"))
    except Exception:
        return {}


def fetch_source_offline(url, benchmark_dir):
    """离线证据导入协议(Air-gapped Evidence Ingestion)优先路径。

    先在本地 source_snapshots/manual/ 查找该 URL 的离线物理快照：
      - 快照文件 <benchmark_dir>/source_snapshots/manual/<sha256>.bin
      - 清单 manifest.json: { "<url>": {"path": "...", "content_hash": "sha256:...", "source_type": ..., "imported_at": ...} }
    若清单命中且 recompute 的 SHA-256 与清单一致 → 返回 (body, text, 200, url)，免在线抓取。
    未命中或哈希不符 → 返回 None，由调用方回退在线 fetch_source。

    返回 (body, text, status, final_url) 或 None。
    """
    from pathlib import Path
    manifest = _lookup_offline_manifest(benchmark_dir)
    entry = manifest.get(url) if manifest else None
    if not entry:
        return None
    rel_path = entry.get("path")
    if not rel_path:
        return None
    snap = Path(benchmark_dir) / rel_path
    if not snap.is_file():
        return None
    body = snap.read_bytes()
    if digest(body) != entry.get("content_hash"):
        return None  # 本地快照被篡改，绝不使用，回退在线
    text = body.decode("utf-8", errors="replace")
    if not text:
        return None
    return body, text, 200, url


def import_offline_snapshot(benchmark_dir, source_url, file_path, source_type="MANUAL_INGEST"):
    """把分析师/爬虫前置落盘的离线证据导入 source_snapshots/manual/ 并登记清单。

    计算固定 SHA-256，写入 <benchmark_dir>/source_snapshots/manual/manifest.json。
    返回写入的凭证条目 dict。
    """
    from pathlib import Path
    import shutil
    import json
    import datetime
    base = Path(benchmark_dir) / "source_snapshots/manual"
    base.mkdir(parents=True, exist_ok=True)
    src = Path(file_path)
    if not src.is_file():
        raise FileNotFoundError(f"Offline source file not found: {file_path}")
    body = src.read_bytes()
    h = digest(body)
    dest = base / (h.split(":")[1] + ".bin")
    shutil.copyfile(src, dest)
    manifest_path = base / "manifest.json"
    manifest = {}
    if manifest_path.is_file():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except Exception:
            manifest = {}
    rel = dest.relative_to(Path(benchmark_dir)).as_posix()
    entry = {
        "path": "source_snapshots/manual/" + dest.name,
        "content_hash": h,
        "source_type": source_type,
        "imported_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }
    manifest[source_url] = entry
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return entry


def calculate(expression, inputs):
    """Bounded arithmetic, never eval; no attributes, calls or indexing."""
    tree = ast.parse(expression, mode='eval')
    if len(list(ast.walk(tree))) > 100:
        raise ValueError('Expression too complex')
    ops = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
           ast.Div: operator.truediv, ast.Pow: operator.pow, ast.USub: operator.neg,
           ast.UAdd: operator.pos}

    def numeric(value):
        if type(value) not in (int, float) or not math.isfinite(value):
            raise ValueError('Expected finite number')
        return value

    def visit(node):
        if isinstance(node, ast.Constant):
            return numeric(node.value)
        if isinstance(node, ast.Name):
            return numeric(inputs[node.id])
        if isinstance(node, ast.UnaryOp) and type(node.op) in (ast.USub, ast.UAdd):
            return numeric(ops[type(node.op)](visit(node.operand)))
        if isinstance(node, ast.BinOp) and type(node.op) in ops:
            a, b = visit(node.left), visit(node.right)
            if isinstance(node.op, ast.Pow) and (abs(a) > 1e6 or abs(b) > 100):
                raise ValueError('Power exceeds limits')
            return numeric(ops[type(node.op)](a, b))
        raise ValueError('Unsupported expression')

    return visit(tree.body)
