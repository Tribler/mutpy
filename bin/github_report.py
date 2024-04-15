from __future__ import annotations

from pathlib import Path

from mutpy import views, controller, operators, utils
from mutpy.test_runners import UnittestTestRunner

def main(project_dirs: list[str], target_files: list[str], unit_test_files: list[str]) -> None:
    """
    Run a mutations on the given target files and check if the given unit test files catch them.

    The (target/test) files should be relative to the project directories.
    """
    top_dir, *paths = [str(Path(pdir).absolute().resolve()) for pdir in project_dirs]
    runner_cls = UnittestTestRunner
    built_views = [views.TextView(colored_output=False, show_mutants=True)]
    mutant_generator = controller.FirstOrderMutator(operators=operators.standard_operators, percentage=100)
    target_loader = utils.ModulesLoader(target_files, path=top_dir)
    test_loader = utils.ModulesLoader(unit_test_files, path=top_dir)
    for folder in paths:
        target_loader.ensure_in_path(folder)
        test_loader.ensure_in_path(folder)
    mutation_controller = controller.MutationController(
        runner_cls=runner_cls,
        target_loader=target_loader,
        test_loader=test_loader,
        views=built_views,
        mutant_generator=mutant_generator
    )
    mutation_controller.run()


if __name__ == "__main__":
    # TODO: Example for single file
    main(["../../TriblerExperimental/src", "../../TriblerExperimental/pyipv8"],
         ["tribler.tribler_config"],
         ["tribler.test_unit.test_tribler_config"])
