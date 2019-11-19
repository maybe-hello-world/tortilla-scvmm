from dataclasses import dataclass


@dataclass(frozen=True)
class VM:
    Name: str
    ID: str
    VirtualMachineState: str
    MostRecentTask: str
    MostRecentTaskUIState: str
    VMHost: str
