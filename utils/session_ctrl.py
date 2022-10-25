from time import sleep, time
from pathlib import Path
import shutil
import pandas as pd
from utils.render_hierarchy_to_html import profile_gpu, profile_cpu
from IPython.display import display, HTML
from remote_execution import RemoteExecution

# -----------------------------------------------------------------------
# common data gather functions


def tail(file, n):
    from collections import deque
    log = file
    with open(log) as fin:
        return list(deque(fin, n))


def gather_all_csv_charts_median_in_folders():
    data_frames = []
    for p in Path.cwd().glob(f'data/*/csvprofile*'):
        header_at_end = tail(p, 2)[0].split(',')
        df = pd.read_csv(
            p, skipfooter=2,
            engine='python', on_bad_lines='skip',
            names=header_at_end, skiprows=1
        ).median()
        data_frames.append(df.to_frame(p.parent.name))
    df = data_frames[0].join(data_frames[1:]).T
    return df


def gather_all_fps_charts_median_in_folders():
    data_frames = []
    for p in Path.cwd().glob(f'data/*/*-fps*.csv'):
        df = pd.read_csv(p, skiprows=4)
        med = df[df.columns.to_list()[:-1]].median().to_frame(p.parent.name)
        data_frames.append(med)
    df = data_frames[0].join(data_frames[1:]).T
    return df


class UnrealEngineConnection():
    def __init__(self, project_saved_folder, project_log, do_init=True, project_commands_plugin='ProfilingBPLibrary'):
        """
        UnrealEngineRemoteExecution class for running tests in session frontend 
        make sure to select session in unreal engine
        expected commands command plugin:
        send_command(FString) -> sends console command to a selected Session in session frontend
        """
        self.project_saved_folder = project_saved_folder
        self.project_name = project_saved_folder.split('\\')[-2]
        self.project_log = project_log

        self.remote_exec = RemoteExecution()
        self.remote_exec.start()
        self.data_folder = Path.cwd().joinpath('data')
        self.project_commands_plugin = project_commands_plugin
        if not self.data_folder.exists():
            self.data_folder.mkdir()
        sleep(1)
        for node in self.remote_exec.remote_nodes:
            if node['project_name'] in self.project_name:
                self.remote_exec.open_command_connection(node.get("node_id"))
        if do_init:
            self.init_build_setup()

    def rc(self, command):
        if self.remote_exec.has_command_connection:
            result = self.remote_exec.run_command(
                f"unreal.{self.project_commands_plugin}.send_command('{command}')")
        else:
            result = 'no connection'
        return result

    def reconnect(self):
        if self.remote_exec.has_command_connection:
            self.remote_exec.close_command_connection()
        for node in self.remote_exec.remote_nodes:
            self.remote_exec.open_command_connection(node.get("node_id"))

    def close_connection(self):
        if self.remote_exec.has_command_connection:
            self.remote_exec.close_command_connection()

    def init_build_setup(self):
        self.rc('t.FPSChart.DoCsvProfile 1')
        self.rc('stat unit')
        self.rc('r.VSync 0')
        self.rc('t.FPSChart.OpenFolderOnDump 0')
        pass

    def count_objects(self):
        self.rc('obj list')
        sleep(1)
        data = []
        log = tail(self.project_log, 500)
        last_profile = 0
        for i, line in enumerate(log):
            if ']Obj List: ' in line:
                last_profile = i
            if last_profile > 0:
                data = log[last_profile:]
        df = pd.DataFrame(data[3:-2])
        df = df[0].str.split(expand=True)
        df.columns = df.iloc[0]
        df = df.drop(0)
        df = df.drop(df.columns[[0]], axis=1)
        df['Count'] = df['Count'].astype("int")
        df = df.sort_values(ascending=False)
        return df

    def read_profile_gpu(self, name='', read_for=1000):
        """
        reads last 'read_for' lines of log to find profilegpu
        result gets copied to clipboard
        returns DataFrame - no hierarchy 
        """
        log = []
        gpu_data = []
        last_profilegpu = 0
        log = tail(self.project_log, read_for)
        for i, line in enumerate(log):
            if 'Profiling the next GPU frame' in line:
                last_profilegpu = i
        gpu_data = log[last_profilegpu:]
        previous_results = Path(f'{name}.html')
        if previous_results.exists():
            previous_results.rename(Path(f'{name}_{int(time())}.html'))
        if last_profilegpu != 0:
            html, df = profile_gpu(gpu_data)
            with open(f'{self.data_folder.resolve()}{name}.html', 'w') as fr:
                fr.write(html)
            display(HTML(html))
            return df
        else:
            print('no profile information found')
            return pd.DataFrame()

    def run_profile_gpu(self, name='', read_for=1000):
        """
        runs profilegpu command
        reads last 'read_for' lines of log to find profilegpu
        result gets copied to clipboard
        returns DataFrame - no hierarchy 
        """
        self.rc('stat unit')
        sleep(0.1)
        self.rc('profilegpu')
        sleep(0.8)
        self.rc('stat unit')
        return self.read_profile_gpu(name, read_for)

    def run_profile_cpu(self, name=''):
        """
        runs DumpFrame command
        reads last 500 lines of log to find DumpFrame
        result gets copied to clipboard
        """
        self.rc('stat unit')
        sleep(0.1)
        self.rc('stat DumpFrame')
        sleep(0.8)
        self.rc('stat unit')
        log = []
        gpu_data = []
        last_profile = 0
        log = tail(self.project_log, 500)
        for i, line in enumerate(log):
            if 'Single Frame ' in line:
                last_profile = i
        gpu_data = log[last_profile:]
        previous_results = Path(f'{name}.html')
        if previous_results.exists():
            previous_results.rename(Path(f'{name}_{int(time())}.html'))
        if last_profile != 0:
            html = profile_cpu(gpu_data)
            with open(f'{self.data_folder.resolve()}{name}.html', 'w') as fr:
                fr.write(html)
            display(HTML(html))
        else:
            print('no profile information found')

    def run_memreport(self, test_name):
        """
        runs command and moves all memreport data from saved folder to data folder
        """
        self.rc('memreport -full')
        sleep(1)
        saved = Path(self.project_saved_folder)
        stats = saved.joinpath('profiling', 'memreports')
        path_for_tests = self.data_folder
        possible_paths = stats.iterdir()
        found_folders = 0
        if stats.exists():
            for index, p in enumerate(possible_paths):
                shutil.copytree(p, path_for_tests.joinpath(
                    f"memreport_{test_name}_{index}"))
                shutil.rmtree(p)
                found_folders += 1
        else:
            print("Can't find memreports")
        if found_folders == 1:
            path_for_tests.joinpath(f"memreport_{test_name}_0").rename(
                path_for_tests.joinpath(f"memreport_{test_name}"))

    def move_fps(self, test_name):
        """
        moves all fps chart data from saved folder
        """
        saved = Path(self.project_saved_folder)
        log = saved.joinpath('logs', f'{self.project_name}.log')
        fps_charts = saved.joinpath('profiling', 'fpschartstats')
        path_for_tests = self.data_folder
        possible_paths = fps_charts.iterdir()
        found_folders = 0
        paths = []
        if fps_charts.exists():
            for index, p in enumerate(possible_paths):
                shutil.copytree(p, path_for_tests.joinpath(
                    f"{test_name}_{index}"))
                shutil.rmtree(p)
                paths.append(path_for_tests.joinpath(
                    f"{test_name}_{index}"))
                found_folders += 1
        else:
            print("Can't find fpschart")
        if found_folders == 1:
            path_for_tests.joinpath(f"{test_name}_0").rename(
                path_for_tests.joinpath(f"{test_name}"))
            return [path_for_tests.joinpath(f"{test_name}")]
        return paths

    def do_fps_chart(self, seconds, test_name: str, wait_for_file=True, wait_time=2,
                     interesting_stats=['FrameTime', 'GPUTime',
                                        'RenderThreadTime', 'GameThreadTime',
                                        'RHIThreadTime', 'RHI/DrawCalls',
                                        'RHI/PrimitivesDrawn']):
        """
        runs fps chart and moves data from saved folder to data folder
        return: Full Csv Chart DataFrame, median interesting_stats DataFrame, median (FrameTime) 
        """
        shutil.rmtree(Path.cwd().joinpath(test_name), ignore_errors=True)
        self.rc('stat unit')
        sleep(0.1)
        self.rc("startfpschart")
        sleep(seconds)
        self.rc("stopfpschart")
        sleep(0.1)
        self.rc('stat unit')
        if wait_for_file:
            sleep(wait_time)
        folders_with_charts = self.move_fps(test_name)
        for folder in folders_with_charts:
            for p in folder.glob(f'csvprofile*'):
                header_at_end = tail(p, 2)[0].split(',')
                df = pd.read_csv(
                    p, skipfooter=2, engine='python', on_bad_lines='skip', names=header_at_end, skiprows=1)
                med = df[interesting_stats].median().to_frame(test_name)
                return df, med, med.loc[['FrameTime'], :][test_name][0]
        return pd.DataFrame(), 0, 0

    def do_simple_fps_chart(self, seconds, test_name: str, wait_for_file=True, wait_time=2):
        """
        runs fps chart and moves data from saved folder to data folder
        return: Full DataFrame, median interesting_stats DataFrame, median (FrameTime) 
        """
        shutil.rmtree(Path.cwd().joinpath(test_name), ignore_errors=True)
        self.rc('stat unit')
        sleep(0.1)
        self.rc("startfpschart")
        sleep(seconds)
        self.rc("stopfpschart")
        sleep(0.1)
        self.rc('stat unit')
        if wait_for_file:
            sleep(wait_time)
        folders_with_charts = self.move_fps(test_name)
        for folder in folders_with_charts:
            for p in folder.glob(f'*-fps*.csv'):
                df = pd.read_csv(p, skiprows=4)
                med = df[df.columns.to_list()[:-1]].median().to_frame(test_name)
                return df, med, df['Frame (ms)'].median()
        return pd.DataFrame(), 0, 0

    # -----------------------------------------------------------------------
    # techart_tools project specific commands

    def open_level(self, level_name:str):
        self.rc(f'open {level_name}')

    def open_level_with_gamemode(self, level_name:str, gamemode_path:str):
        self.rc(f'open {level_name}?game={gamemode_path}')

    def stream_level_in(self, level_path:str):
        self.rc(f'streamLevelIn {level_path}')

    def stream_level_out(self, level_path:str):
        self.rc(f'streamLevelOut {level_path}')

    def do_enchanted_input_action(self, action:str):
        self.rc(f'input.+action {action}')
