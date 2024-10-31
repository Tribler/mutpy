from __future__ import annotations

import argparse
import ast
import glob
import inspect
from difflib import unified_diff
from pathlib import Path
from typing import Generator

from mutpy import controller, operators, utils, codegen
from mutpy.operators import OverriddenMethodCallingPositionChange
from mutpy.test_runners import UnittestTestRunner
from mutpy.views import AccReportView

EMOJI_MAP = {
    "survived": "❌",
    "killed": "✅"
}

MUTATION_OPS = {
    op for op in operators.standard_operators
    if op != OverriddenMethodCallingPositionChange
}


class GitHubView(AccReportView):

    def __init__(self, target_file: str) -> None:
        super().__init__()
        self.content = f"## {target_file}\n"

    @staticmethod
    def _create_diff(mutant_src, original_src):
        return list(unified_diff(original_src.split('\n'), mutant_src.split('\n'), n=0, lineterm=''))

    def get_diff(self, mutant_src, original_src):
        diff = self._create_diff(mutant_src, original_src)
        diff = [line for line in diff if not line.startswith(('---', '+++', '@@'))]
        return "\n".join(diff)

    def styled_diff(self, mutant, original):
        mutant_src = codegen.to_source(mutant)
        mutant_src = codegen.add_line_numbers(mutant_src)
        original_src = codegen.to_source(original)
        original_src = codegen.add_line_numbers(original_src)
        return self.get_diff(mutant_src, original_src)

    def mutation(self, number, mutations, module, mutant):
        super().mutation(number, mutations, module, mutant)
        self.current_mutation['mutant'] = mutant
        self.current_mutation['module_src'] = ast.parse(inspect.getsource(module))

    def end_mutation(self, status, time=None, killer=None, tests_run=None, exception_traceback=None):
        super().end_mutation(status, time, killer, tests_run, exception_traceback)
        diff = self.styled_diff(self.current_mutation['mutant'], self.current_mutation['module_src'])
        self.content += (f"<details><summary>{EMOJI_MAP.get(status, '➿')} "
                         f"{self.current_mutation['mutations'][0]['operator']}"
                         f"@{self.current_mutation['mutations'][0]['lineno']} {status}</summary>\n\n"
                         f"```patch\n{diff}\n```\n\n</details>\n\n")

def run(project_dirs: list[str], target_file: str, unit_test_file: str) -> GitHubView:
    """
    Run a mutations on the given target files and check if the given unit test files catch them.

    The (target/test) files should be relative to the project directories.
    """
    top_dir, *paths = [str(Path(pdir).absolute().resolve()) for pdir in project_dirs]
    runner_cls = UnittestTestRunner
    viewer = GitHubView(target_file)
    mutant_generator = controller.FirstOrderMutator(operators=MUTATION_OPS, percentage=100)
    target_loader = utils.ModulesLoader([target_file], path=top_dir)
    test_loader = utils.ModulesLoader([unit_test_file], path=top_dir)
    for folder in paths:
        target_loader.ensure_in_path(folder)
        test_loader.ensure_in_path(folder)
    mutation_controller = controller.MutationController(
        runner_cls=runner_cls,
        target_loader=target_loader,
        test_loader=test_loader,
        views=[viewer],
        mutant_generator=mutant_generator
    )
    mutation_controller.run()
    return viewer


def module_name(src_dir: str, target: str, prefix: str) -> str:
    return prefix + ".".join(Path(target[:-3]).relative_to(src_dir).parts)


def run_from_dirs(project_dirs: list[str], src_dir: str, test_dir: str,
                  prefix: str) -> Generator[GitHubView, None, None]:
    test_files = glob.glob(f"{test_dir}/**/test_*.py", recursive=True)
    for test_file in test_files:
        relpath = (Path(src_dir) / Path(test_file).relative_to(test_dir))
        target = str(relpath.parent / relpath.name[5:])
        print("Processing", module_name(src_dir, target, prefix), "<-", module_name(src_dir, test_file, prefix))
        yield run(project_dirs, module_name(src_dir, target, prefix), module_name(src_dir, test_file, prefix))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--codebase", choices=["ipv8", "tribler", "triblerexp"], required=True)
    args = parser.parse_args()

    if args.codebase == "ipv8":
        project_directories = ["../../py-ipv8"]
        src_dir = "../../py-ipv8/ipv8"
        test_dir = "../../py-ipv8/ipv8/test"
        prefix = "ipv8."
    elif args.codebase == "tribler":
        project_directories = ["../../tribler/src", "../../tribler/pyipv8"]
        src_dir = "../../tribler/src/tribler"
        test_dir = "../../tribler/src/tribler/test_unit"
        prefix = "tribler."
    elif args.codebase == "triblerexp":
        project_directories = ["../../TriblerExperimental/src", "../../TriblerExperimental/pyipv8"]
        src_dir = "../../TriblerExperimental/src/tribler"
        test_dir = "../../TriblerExperimental/src/tribler/test_unit"
        prefix = "tribler."
    else:
        raise RuntimeError("How did you get here?")

    with open("report.md", "wb") as file_stream:
        for viewer in run_from_dirs(project_directories, src_dir, test_dir, prefix):
            file_stream.write(viewer.content.encode())


if __name__ == "__main__":
    main()
