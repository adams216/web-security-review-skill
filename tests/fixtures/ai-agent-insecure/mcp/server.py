import subprocess


def run_shell(command: str) -> str:
    completed = subprocess.run(command, shell=True, capture_output=True, text=True)
    return completed.stdout
