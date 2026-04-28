import subprocess
from pathlib import Path


class ExecResult:
    def __init__(self, exit_code: int, error: str | None):
        self.exit_code = exit_code
        self.error = error


def run_cmd(
    args: list[str],
    cwd: Path,
    log_path: Path,
    env: dict[str, str] | None = None,
    append: bool = False,
) -> ExecResult:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    mode = "a" if append else "w"
    with log_path.open(mode, encoding="utf-8") as f:
        f.write(f"$ {' '.join(args)}\n")
        f.flush()
        try:
            proc = subprocess.Popen(
                args,
                cwd=str(cwd),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                env=env,
            )
        except OSError as e:
            f.write(f"spawn_error: {e}\n")
            return ExecResult(exit_code=127, error=str(e))

        assert proc.stdout is not None
        for line in proc.stdout:
            f.write(line)
        proc.wait()
        return ExecResult(exit_code=int(proc.returncode or 0), error=None)

