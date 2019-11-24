import uvicorn
import logging
from fastapi import FastAPI
from pypsrp.wsman import WSMan
from pypsrp.powershell import PowerShell, RunspacePool
from requests.exceptions import ReadTimeout, ConnectTimeout
from starlette.responses import RedirectResponse, Response

import scvmmapi.config as config
from data.VM import VM
from scvmmapi.utils import NoHeaderErrorFilter, LIST_SCRIPT

app = FastAPI(
    title="SCVMM-api",
    description="Simple SCVMM api for executing commands to control VMs.",
    version="0.1.0"
)

wsman: WSMan
pool: RunspacePool

logging.getLogger("urllib3.connectionpool").addFilter(
    NoHeaderErrorFilter()
)


@app.on_event("startup")
async def __init__():
    global wsman, pool
    connection_settings = config.SETTINGS.get("connection", {})
    wsman = WSMan(
        server=config.CONN_HOST,
        username=config.CONN_LOGIN,
        password=config.CONN_PASSWORD,
        **connection_settings
    )

    pool_settings = config.SETTINGS.get("pool", {})
    pool = RunspacePool(
        connection=wsman,
        **pool_settings
    )
    try:
        pool.open()
    except ConnectTimeout:
        logging.error(f"Cannot connect to SCVMM host {config.CONN_HOST}, exiting...")
        raise
    else:
        logging.info(f"RunspacePool opened, min threads: {pool.min_runspaces}, max threads: {pool.max_runspaces}")


@app.on_event("shutdown")
def __del__():
    global pool
    pool.close()


@app.get("/")
async def root():
    """
    Show this docs
    """
    return RedirectResponse(url='/docs')


@app.post("/api/vm/start", status_code=204)
async def start_vm(vmid: str):
    """
    Invoke command to start virtual machine with given VM ID
    :param vmid: VM ID of virtual machine to be started
    """
    (PowerShell(pool)
     .add_script("Get-SCVirtualMachine | ? {$_.VMId -eq \"" + vmid + "\" } | Start-SCVirtualMachine")
     .begin_invoke())


@app.post("/api/vm/save", status_code=204)
async def save_vm(vmid: str):
    """
    Invoke command to save virtual machine with given VM ID
    :param vmid: VM ID of virtual machine to be saved
    """
    (PowerShell(pool)
     .add_script("Get-SCVirtualMachine | ? {$_.VMId -eq \"" + vmid + "\" } | Stop-SCVirtualMachine -SaveState")
     .begin_invoke())


@app.post("/api/vm/shutdown", status_code=204)
async def shutdown_vm(vmid: str):
    """
    Invoke command to shutdown virtual machine with given VM ID
    :param vmid: VM ID of virtual machine to be shutdowned
    """
    (PowerShell(pool)
     .add_script("Get-SCVirtualMachine | ? {$_.VMId -eq \"" + vmid + "\" } | Stop-SCVirtualMachine -Shutdown")
     .begin_invoke())


@app.post("/api/vm/poweroff", status_code=204)
async def poweroff_vm(vmid: str):
    """
    Invoke command to forcefully shutdown virtual machine with given VM ID
    :param vmid: VM ID of virtual machine to be forcefully shutdowned
    """
    (PowerShell(pool)
     .add_script("Get-SCVirtualMachine | ? {$_.VMId -eq \"" + vmid + "\" } | Stop-SCVirtualMachine -Force")
     .begin_invoke())


@app.get("/api/vm/list")
async def list_vms(domain: str, username: str):
    """
    Returns a list of available virtual machines for given user
    :param domain: NTDOMAIN of the user
    :param username: username of the user
    :return: list of dicts with virtual machines data
    """
    domain = domain.upper()
    username = username.lower()

    if LIST_SCRIPT is None:
        return Response(status_code=500, content="Server error: script not found.")

    ps = PowerShell(pool)
    ps.add_script(script=LIST_SCRIPT).add_argument(domain).add_argument(username)
    try:
        psresult = ps.invoke()
    except ReadTimeout:
        return Response(status_code=504, content="SCVMM is not available now.")

    if len(psresult) == 0 and ps.had_errors:
        return Response(status_code=500, content="SCVMM-API internal error occured.")

    if psresult:
        logging.info(f"Data for {domain}\\{username} returned, length: {len(psresult)}")

    return [
        VM(
            Name=x.extended_properties.get("Name", "-"),
            ID=x.extended_properties.get("VMId", "-"),
            VirtualMachineState=x.extended_properties.get('VirtualMachineState', "-"),
            MostRecentTask=x.extended_properties.get('MostRecentTask', "-"),
            MostRecentTaskUIState=x.extended_properties.get('MostRecentTaskUIState', "-"),
            VMHost=x.extended_properties.get('VMHost', "-")
        )
        for x in psresult
    ]


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5555)
