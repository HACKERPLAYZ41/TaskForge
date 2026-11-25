"""AST-based codebase analyzer for task extraction."""
import ast
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Set
from taskforge.adapters.base import RepoAdapter

@dataclass
class FunctionSignature:
    name: str
    args: List[str]
    docstring: str = ""
    lineno: int = 0

@dataclass
class ClassInfo:
    name: str
    bases: List[str]
    methods: List[FunctionSignature] = field(default_factory=list)
    docstring: str = ""
    lineno: int = 0

@dataclass
class ModuleAnalysis:
    path: str
    relative_path: str
    classes: List[ClassInfo] = field(default_factory=list)
    functions: List[FunctionSignature] = field(default_factory=list)
    imports: List[str] = field(default_factory=list)
    loc: int = 0

@dataclass
class RepoAnalysis:
    repo_path: str
    commit_hash: str
    modules: Dict[str, ModuleAnalysis] = field(default_factory=dict)
    test_files: List[str] = field(default_factory=list)
    total_loc: int = 0
    dependency_graph: Dict[str, Set[str]] = field(default_factory=dict)

class CodeAnalyzer:
    def __init__(self, adapter: RepoAdapter):
        self.adapter = adapter

    def analyze(self) -> RepoAnalysis:
        repo_path = str(self.adapter.repo_path)
        commit = self.adapter.get_commit_hash()
        modules = {}
        total_loc = 0
        dep_graph: Dict[str, Set[str]] = {}

        for mod_path in self.adapter.list_modules():
            rel_str = str(mod_path.relative_to(self.adapter.repo_path))
            try:
                content = mod_path.read_text(encoding="utf-8")
                tree = ast.parse(content, filename=str(mod_path))
                loc = len(content.splitlines())
                total_loc += loc

                classes = []
                functions = []
                imports = []

                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            imports.append(alias.name)
                    elif isinstance(node, ast.ImportFrom):
                        mod = node.module or ""
                        imports.append(mod)

                for item in tree.body:
                    if isinstance(item, ast.ClassDef):
                        bases = [b.id for b in item.bases if isinstance(b, ast.Name)]
                        methods = []
                        for sub in item.body:
                            if isinstance(sub, ast.FunctionDef):
                                args = [a.arg for a in sub.args.args]
                                doc = ast.get_docstring(sub) or ""
                                methods.append(FunctionSignature(name=sub.name, args=args, docstring=doc, lineno=sub.lineno))
                        c_doc = ast.get_docstring(item) or ""
                        classes.append(ClassInfo(name=item.name, bases=bases, methods=methods, docstring=c_doc, lineno=item.lineno))
                    elif isinstance(item, ast.FunctionDef):
                        args = [a.arg for a in item.args.args]
                        doc = ast.get_docstring(item) or ""
                        functions.append(FunctionSignature(name=item.name, args=args, docstring=doc, lineno=item.lineno))

                dep_graph[rel_str] = set(imports)
                modules[rel_str] = ModuleAnalysis(
                    path=str(mod_path),
                    relative_path=rel_str,
                    classes=classes,
                    functions=functions,
                    imports=imports,
                    loc=loc
                )
            except Exception:
                continue

        tests = [str(p.relative_to(self.adapter.repo_path)) for p in self.adapter.list_tests()]
        return RepoAnalysis(
            repo_path=repo_path,
            commit_hash=commit,
            modules=modules,
            test_files=tests,
            total_loc=total_loc,
            dependency_graph=dep_graph
        )
