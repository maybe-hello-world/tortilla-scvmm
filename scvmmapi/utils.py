import logging


def get_pwsh_script(path: str) -> str:
    """
    Get the contents of a script stored in pypsrp/pwsh_scripts. Will also strip out any empty lines and comments to
    reduce the data we send across as much as possible.
    Source: https://github.com/jborean93/pypsrp
    :param path: The filename of the script in pypsrp/pwsh_scripts to get.
    :return: The script contents.
    """
    with open(path, "rt") as f:
        script = f.readlines()

    block_comment = False
    new_lines = []
    for line in script:

        line = line.strip()
        if block_comment:
            block_comment = not line.endswith('#>')
        elif line.startswith('<#'):
            block_comment = True
        elif line and not line.startswith('#'):
            new_lines.append(line)

    return '\n'.join(new_lines)


class NoHeaderErrorFilter(logging.Filter):
    """Filter out urllib3 Header Parsing Errors due to a urllib3 bug."""

    def filter(self, record):
        """Filter out Header Parsing Errors."""
        return "Failed to parse headers" not in record.getMessage()


list_script_path = "scripts/list.ps1"
LIST_SCRIPT = None
try:
    LIST_SCRIPT = get_pwsh_script(list_script_path)
except OSError:
    logging.error(f"Script {list_script_path} was not found!")
