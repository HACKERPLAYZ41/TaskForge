"""AST-based Mutation Engine for G3 (mutation test) and G4 (regression sensitivity).
Implements 9 AST operators producing >= 15 mutants per task with unified diffs.
"""
import ast
import difflib
import random
from typing import Any, Dict, List, Optional, Tuple

class MutationVisitor(ast.NodeTransformer):
    def __init__(self, mutation_type: str, seed: int = 42, target_idx: int = 0):
        super().__init__()
        self.mutation_type = mutation_type
        self.rng = random.Random(seed)
        self.target_idx = target_idx
        self.current_idx = 0
        self.applied = False

    def _should_apply(self) -> bool:
        if self.applied:
            return False
        if self.current_idx == self.target_idx:
            self.applied = True
            return True
        self.current_idx += 1
        return False

    def visit_Compare(self, node: ast.Compare) -> ast.AST:
        if self.mutation_type != "flip_comparison":
            return self.generic_visit(node)
        if not self._should_apply():
            return self.generic_visit(node)

        new_ops = []
        for op in node.ops:
            if isinstance(op, ast.Lt):
                new_ops.append(ast.GtE())
            elif isinstance(op, ast.Gt):
                new_ops.append(ast.LtE())
            elif isinstance(op, ast.Eq):
                new_ops.append(ast.NotEq())
            elif isinstance(op, ast.NotEq):
                new_ops.append(ast.Eq())
            elif isinstance(op, ast.LtE):
                new_ops.append(ast.Gt())
            elif isinstance(op, ast.GtE):
                new_ops.append(ast.Lt())
            elif isinstance(op, ast.In):
                new_ops.append(ast.NotIn())
            elif isinstance(op, ast.NotIn):
                new_ops.append(ast.In())
            else:
                new_ops.append(op)
        node.ops = new_ops
        return node

    def visit_Constant(self, node: ast.Constant) -> ast.AST:
        if self.mutation_type == "off_by_one":
            if isinstance(node.value, int) and not isinstance(node.value, bool):
                if self._should_apply():
                    delta = 1 if self.target_idx % 2 == 0 else -1
                    node.value = node.value + delta
        elif self.mutation_type == "invert_boolean":
            if isinstance(node.value, bool):
                if self._should_apply():
                    node.value = not node.value
        return node

    def visit_Return(self, node: ast.Return) -> ast.AST:
        if self.mutation_type != "return_default":
            return self.generic_visit(node)
        if self._should_apply():
            val = None if self.target_idx % 3 == 0 else (0 if self.target_idx % 3 == 1 else False)
            node.value = ast.Constant(value=val)
        return node

    def visit_If(self, node: ast.If) -> ast.AST:
        if self.mutation_type == "remove_branch":
            if self._should_apply():
                node.body = [ast.Pass()]
                return node
        elif self.mutation_type == "drop_validation":
            has_raise = any(isinstance(s, ast.Raise) for s in node.body)
            if has_raise and self._should_apply():
                node.body = [ast.Pass()]
                return node
        return self.generic_visit(node)

    def visit_BoolOp(self, node: ast.BoolOp) -> ast.AST:
        if self.mutation_type != "invert_boolean":
            return self.generic_visit(node)
        if self._should_apply():
            if isinstance(node.op, ast.And):
                node.op = ast.Or()
            elif isinstance(node.op, ast.Or):
                node.op = ast.And()
        return self.generic_visit(node)

    def visit_UnaryOp(self, node: ast.UnaryOp) -> ast.AST:
        if self.mutation_type != "invert_boolean":
            return self.generic_visit(node)
        if isinstance(node.op, ast.Not) and self._should_apply():
            return node.operand
        return self.generic_visit(node)

    def visit_BinOp(self, node: ast.BinOp) -> ast.AST:
        if self.mutation_type != "binary_op":
            return self.generic_visit(node)
        if self._should_apply():
            if isinstance(node.op, ast.Add):
                node.op = ast.Sub()
            elif isinstance(node.op, ast.Sub):
                node.op = ast.Add()
            elif isinstance(node.op, ast.Mult):
                node.op = ast.Div()
            elif isinstance(node.op, ast.Div):
                node.op = ast.Mult()
        return self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> ast.AST:
        if self.mutation_type != "swap_arguments":
            return self.generic_visit(node)
        if len(node.args) >= 2 and self._should_apply():
            node.args[0], node.args[1] = node.args[1], node.args[0]
        return self.generic_visit(node)

    def visit_ExceptHandler(self, node: ast.ExceptHandler) -> ast.AST:
        if self.mutation_type != "swallow_exception":
            return self.generic_visit(node)
        if self._should_apply():
            node.body = [ast.Pass()]
        return self.generic_visit(node)

class CodeMutator:
    MUTATION_TYPES = [
        "flip_comparison",
        "off_by_one",
        "remove_branch",
        "return_default",
        "drop_validation",
        "invert_boolean",
        "binary_op",
        "swap_arguments",
        "swallow_exception"
    ]

    def mutate_source(self, source_code: str, mutation_type: str, target_idx: int = 0, seed: int = 42) -> Optional[str]:
        try:
            tree = ast.parse(source_code)
            transformer = MutationVisitor(mutation_type, seed=seed, target_idx=target_idx)
            mutated_tree = transformer.visit(tree)
            if not transformer.applied:
                return None
            ast.fix_missing_locations(mutated_tree)
            return ast.unparse(mutated_tree)
        except Exception:
            return None

    def generate_mutants(self, source_code: str, min_count: int = 15, seed: int = 42) -> List[Dict[str, Any]]:
        """Generates at least min_count distinct mutants with unified diffs."""
        mutants: List[Dict[str, Any]] = []
        seen_codes = {source_code}

        for round_idx in range(6):
            for m_type in self.MUTATION_TYPES:
                for target_idx in range(8):
                    mutated = self.mutate_source(source_code, m_type, target_idx=target_idx, seed=seed + len(mutants))
                    if mutated and mutated != source_code and mutated not in seen_codes:
                        seen_codes.add(mutated)
                        diff = "\n".join(difflib.unified_diff(
                            source_code.splitlines(),
                            mutated.splitlines(),
                            fromfile="original.py",
                            tofile=f"mutant_{len(mutants) + 1}.py",
                            lineterm=""
                        ))
                        mutants.append({
                            "mutant_id": f"M{len(mutants) + 1:02d}",
                            "operator": m_type,
                            "target_idx": target_idx,
                            "mutated_code": mutated,
                            "diff": diff
                        })
                        if len(mutants) >= min_count:
                            return mutants

        return mutants
