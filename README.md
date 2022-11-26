# Unreal Profiling With Python

Jupyter Notebook has many useful tools to visualize data gathered from Unreal Engine games

This repository has code to start gathering and visualizing data from UE games via Session Fronted and Jupyter Notebook

# How to start using 

run **get_dependencies.bat** to get remote execution from https://github.com/EpicGames/BlenderTools and create venv

run **set_local_paths.bat** to add dependencies paths into venv

## Runnning profiling_project 
Profiling_project is a container Project for ProfilingBPLibrary cpp plugin that exposes https://docs.unrealengine.com/5.1/en-US/API/Runtime/SessionServices/ISessionInstanceInfo/ExecuteCommand/ to Blueprints/Python

* run profiling_project/profiling_project.uproject
* Enable Remote Execution in Unreal

    Project Settings -> Plugins -> Python -> Python Remote Execution -> Enable Remote Execution = True

## Jupyter Notebook Setup

Minimal code for unreal engine connection and command sending:
```
from remote_execution import RemoteExecution
remote_exec = RemoteExecution()
remote_exec.start()
for node in remote_exec.remote_nodes:
    remote_exec.open_command_connection(node.get("node_id"))
remote_exec.run_command(f"unreal.ProfilingBPLibrary.send_command('stat unitgraph')")
```

example in [test_example.ipynb](test_example/test_example.ipynb)


## How to run game so it's visible in Session Frontend
Add argument **-Messaging** when you run builds

example command to run on windows - [profiling_project\Script\run_on_external_machine.bat](run_on_external_machine.bat)

Machines on local network should be added in

Project Settings -> Plugins -> UDP Messaging -> Static Endpoints 

or Engine.ini 
```
[/Script/UdpMessaging.UdpMessagingSettings]
StaticEndpoints=192.168.**.***:6666
```

# utils - session_ctrl

Designed to be used with Jupyter Notebook to automate gathering and visualization of Unreal Engine profiling commands like profilegpu, StartFpsChart and StopFpsChart

usage example in notebook [test_example.ipynb](test_example/test_example.ipynb)


