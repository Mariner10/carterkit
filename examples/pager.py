"""Page your phone to approve an agent action.  Run: python3 examples/pager.py"""
import sys

from carterkit import Hub
from carterkit.pager import AgentPager, build_pager_layout
from _common import hub_for, main  # noqa: F401


async def run(hub, **pager_kw):
    async with hub:
        pager = await AgentPager(hub, **pager_kw).start(serve_socket=False)
        try:
            print("Paging your phone; approve or deny it there (times out = deny)...")
            decision = await pager.ask("demo-agent", "Bash", "rm -rf build/")
            print("Decision:", decision)
            return decision
        finally:
            await pager.stop()


class _Ui:
    """main() wants something with .serve(); the pager hub is built from its own layout."""
    @staticmethod
    def serve(path):
        return Hub(build_pager_layout(), path)


if __name__ == "__main__":
    sys.exit(main(run, _Ui))
