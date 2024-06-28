import os
import json
import aiohttp
import asyncio
import zipfile
import yaml
import shutil
from colorama import Fore, Back, Style
from easygui import diropenbox

class Console:
    INFO = " INFO "
    ERROR = " ERROR "
    APP = " APP "

    def __init__(self):
        self.logs = []

    @staticmethod
    def text(msg: str = "", prefix: str = "", text_color: str = Fore.RESET, back_color: str = Fore.RESET, prefix_text_color: str = Fore.RESET, prefix_back_color: str = Fore.RESET):
        return f"{prefix_text_color}{prefix_back_color}{prefix}{Style.RESET_ALL} {text_color}{back_color}{msg}{Style.RESET_ALL}"

    def save_logs(self):
        logs = "\r".join(self.logs)
        with open("latest.log", "w+", encoding="UTF-8") as file:
            file.write(logs)

    def save_log(self, log: str):
        self.logs.append(log)
        self.save_logs()

    def log(self, msg: str = "", prefix: str = "", text_color: str = Fore.RESET, back_color: str = Back.RESET, prefix_text_color: str = Fore.RESET, prefix_back_color: str = Back.RESET):
        print(Console.text(msg=msg, prefix=prefix, text_color=text_color, back_color=back_color, prefix_text_color=prefix_text_color, prefix_back_color=prefix_back_color))
        self.save_log(f"[{prefix}] {msg}")

    def info(self, msg: str):
        self.log(msg=msg, prefix=self.INFO, prefix_text_color=Fore.BLACK, prefix_back_color=Back.YELLOW)

    def error(self, msg: str, reason: str):
        print(Console.text(msg=f"{msg}: {Fore.LIGHTRED_EX}{reason}{Style.RESET_ALL}", prefix=self.ERROR, prefix_text_color=Fore.BLACK, prefix_back_color=Back.LIGHTRED_EX))
        self.save_log(f"[{self.ERROR}] {msg}: {reason}")

    def app(self, msg: str):
        self.log(msg=msg, prefix=self.APP, prefix_text_color=Fore.BLACK, prefix_back_color=Back.LIGHTCYAN_EX)

    def downloading(self, mod_name: str, mod_version: str):
        self.log(msg=f"{mod_name} v{mod_version}", prefix=" Downloading ", prefix_text_color=Fore.BLACK, prefix_back_color=Back.LIGHTBLUE_EX)

    def downloaded(self, mod_name: str, mod_version: str):
        self.log(msg=f"{mod_name} v{mod_version}", prefix=" Downloaded ", prefix_text_color=Fore.BLACK, prefix_back_color=Back.LIGHTYELLOW_EX)

    def installed(self, mod_name: str, mod_version: str):
        self.log(msg=f"{mod_name} v{mod_version}", prefix=" Installed ", prefix_text_color=Fore.BLACK, prefix_back_color=Back.GREEN)

console = Console()

class SharedVars:
    def __init__(self):
        self.GAME_FOLDER = None
        self.BEPINEX_FOLDER = None
        self.PLUGINS_FOLDER = None
        self.TEMP_FOLDER = "temp"

    def set_game_path(self, path):
        self.GAME_FOLDER = path
        self.BEPINEX_FOLDER = os.path.join(self.GAME_FOLDER, "BepInEx")
        self.PLUGINS_FOLDER = os.path.join(self.BEPINEX_FOLDER, "plugins")

shared_vars = SharedVars()

class ModStructure:
    def __init__(self):
        self.structure = None
        self.structure_mod_files = []
        self.structure_subfolders = []
        self.structure_root_files = []
        self.root_path = None
        self.extraction_path = None

    def get_folders(self, folder):
        folders = list(filter(lambda x: os.path.isdir(os.path.join(folder, x.lower())), os.listdir(folder)))
        return folders

    def get_files(self, folder):
        files = list(filter(lambda x: os.path.isfile(os.path.join(folder, x.lower())), os.listdir(folder)))
        return files

    def is_subfolder(self, folders):
        possible_folders = ["plugins", "config", "core", "patchers"]
        if list(filter(lambda x: x in folders, possible_folders)):
            return True
        return False

    def set_structure_data(self, structure, root_path, extraction_path):
        self.structure = structure
        self.root_path = root_path
        self.extraction_path = extraction_path

    def define_mod_structure(self, temp_folder, mod_folder):
        folders = self.get_folders(temp_folder)
        files = self.get_files(temp_folder)
        
        mod_files = ["manifest.json", "readme.md", "changelog.md", "license", "icon.png"]

        self.structure_mod_files += list(filter(lambda x: x.lower() in mod_files, files))

        if list(filter(lambda x: os.path.exists(os.path.join(temp_folder, "BepInEx")), folders)):
            subfolders = self.get_folders(os.path.join(temp_folder, "BepInEx"))
            self.structure_root_files = list(filter(lambda x: x.lower() not in mod_files, (self.get_files(temp_folder))))
            self.structure_subfolders = subfolders
            self.set_structure_data("bepinex", temp_folder, shared_vars.GAME_FOLDER)
        elif self.is_subfolder(folders):
            self.structure_subfolders = folders
            self.set_structure_data("subfolder", temp_folder, shared_vars.BEPINEX_FOLDER)
        else:
            if list(filter(lambda x: x.lower().endswith(".dll"), files)) or list(filter(lambda x: x.lower().endswith(".cosmetics"), files)):
                self.set_structure_data("dll", temp_folder, mod_folder)
            else:
                for folder in folders:
                    subfolders = self.get_folders(os.path.join(temp_folder, folder))
                    subfiles = self.get_files(os.path.join(temp_folder, folder))
                    if self.is_subfolder(subfolders):
                        self.structure_subfolders = subfolders
                        self.set_structure_data("other/subfolder", os.path.join(temp_folder, folder), shared_vars.BEPINEX_FOLDER)
                    elif list(filter(lambda x: os.path.exists(os.path.join(temp_folder, folder, "BepInEx")), subfolders)):
                        subfolders = self.get_folders(os.path.join(temp_folder, folder, "BepInEx"))
                        self.structure_root_files = list(filter(lambda x: x.lower() not in mod_files, (self.get_files(os.path.join(temp_folder, folder)))))
                        self.structure_subfolders = subfolders
                        self.set_structure_data("other/bepinex", os.path.join(temp_folder, folder), shared_vars.GAME_FOLDER)
                    elif list(filter(lambda x: x.lower().endswith(".dll"), subfiles)):
                        self.set_structure_data("other/dll", os.path.join(temp_folder, folder), mod_folder)
    
class Mod:
    def __init__(self, name, author):
        self.name = name
        self.author = author

        self.folder_name = f"{author}-{name}"
        self.temp_folder = os.path.join(shared_vars.TEMP_FOLDER, self.folder_name)
        self.mod_folder = os.path.join(shared_vars.PLUGINS_FOLDER, self.folder_name)

        self.local_version = None
        self.latest_version = None

        self.structure = ModStructure()
        self.download_url = None
        self.is_updated = False

    async def fetch_info(self):
        while True:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(f"https://thunderstore.io/api/experimental/package/{self.author}/{self.name}/") as response:
                        if response.status == 200:
                            request = await response.json()

                            self.download_url = request["latest"]["download_url"]
                            self.latest_version = request["latest"]["version_number"]

                            if self.exists_locally():
                                if self.get_local_version() == self.latest_version:
                                    self.is_updated = True
                            break
            except (aiohttp.ClientResponseError, aiohttp.ClientOSError, aiohttp.ClientConnectorError):
                await asyncio.sleep(1)
            except Exception:
                break

    def exists_locally(self):
        return os.path.exists(os.path.join(self.mod_folder, "manifest.json"))

    def get_local_version(self):
        with open(os.path.join(self.mod_folder, "manifest.json"), "r", encoding="utf-8-sig") as f:
            return json.load(f)["version_number"]

    async def download_mod(self):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.download_url) as response:
                    with open(os.path.join(shared_vars.TEMP_FOLDER, f"{self.folder_name}.zip"), "wb") as file:
                        file.write(await response.content.read())

                with zipfile.ZipFile(os.path.join(shared_vars.TEMP_FOLDER, f"{self.folder_name}.zip"), "r") as file:
                    file.extractall(os.path.join(self.temp_folder))

                os.remove(os.path.join(shared_vars.TEMP_FOLDER, f"{self.folder_name}.zip"))

                console.downloaded(self.name, self.latest_version)
        except Exception as e:
            console.error(f"Error downloading {self.name}", e)

    def handle_bepinex(self):
        if "plugins" in [i.lower() for i in self.structure.structure_subfolders]:
            if list(filter(lambda x: os.path.isfile(os.path.join(self.structure.root_path, "BepInEx", "plugins", x.lower())), os.listdir(os.path.join(self.structure.root_path, "BepInEx", "plugins")))):
                shutil.copytree(os.path.join(self.structure.root_path, "BepInEx", "plugins"), self.mod_folder, dirs_exist_ok=True)
            plugins_folders = list(filter(lambda x: os.path.isdir(os.path.join(self.structure.root_path, "BepInEx", "plugins", x.lower())), os.listdir(os.path.join(self.structure.root_path, "BepInEx", "plugins"))))
            if plugins_folders:
                if self.folder_name not in plugins_folders:
                    shutil.copytree(os.path.join(self.structure.root_path, "BepInEx", "plugins"), self.mod_folder, dirs_exist_ok=True)
            shutil.rmtree(os.path.join(self.structure.root_path, "BepInEx", "plugins"), ignore_errors=True)

        for mod_file in self.structure.structure_root_files:
            if not mod_file.endswith(".txt"):
                shutil.move(os.path.join(self.structure.root_path, mod_file), shared_vars.GAME_FOLDER)

        shutil.copytree(os.path.join(self.structure.root_path, "BepInEx"), os.path.join(self.structure.extraction_path, "BepInEx"), dirs_exist_ok=True)

    def handle_subfolder(self):
        if "plugins" in [i.lower() for i in self.structure.structure_subfolders]:
            if list(filter(lambda x: os.path.isfile(os.path.join(self.structure.root_path, "plugins", x.lower())), os.listdir(os.path.join(self.structure.root_path, "plugins")))):
                shutil.copytree(os.path.join(self.structure.root_path, "plugins"), self.mod_folder, dirs_exist_ok=True)
            plugins_folders = list(filter(lambda x: os.path.isdir(os.path.join(self.structure.root_path, "plugins", x.lower())), os.listdir(os.path.join(self.structure.root_path, "plugins"))))
            if plugins_folders:
                if self.folder_name not in plugins_folders:
                    shutil.copytree(os.path.join(self.structure.root_path, "plugins"), self.mod_folder, dirs_exist_ok=True)
            shutil.rmtree(os.path.join(self.structure.root_path, "plugins"), ignore_errors=True)
        for subfolder in self.structure.structure_subfolders:
            if not os.path.exists(os.path.join(self.structure.root_path, subfolder)):
                continue
            shutil.copytree(os.path.join(self.structure.root_path, subfolder), os.path.join(self.structure.extraction_path, subfolder), dirs_exist_ok=True)
    
    def handle_dll(self):
        shutil.copytree(self.structure.root_path, os.path.join(self.structure.extraction_path, self.folder_name), dirs_exist_ok=True)

    async def install_mod(self):
        self.structure.define_mod_structure(self.temp_folder, self.mod_folder)

        os.makedirs(self.mod_folder, exist_ok=True)

        for mod_file in self.structure.structure_mod_files:
            shutil.move(os.path.join(self.temp_folder, mod_file), self.mod_folder)

        match self.structure.structure:
            case "bepinex":
                self.handle_bepinex()
            case "subfolder":
                self.handle_subfolder()
            case "dll":
                self.handle_dll()
            case "other/bepinex":
                self.handle_bepinex()
            case "other/subfolder":
                self.handle_subfolder()
            case "other/dll":
                self.handle_dll()
            case _:
                console.error(f"Failed to install {self.name} v{self.latest_version}", "Installer didn't return any valid structure")
                return

        console.installed(self.name, self.latest_version)

class App:
    def __init__(self):
        self.mod_list: list[Mod] = []
        self.mods_to_download: list[Mod] = []

    def get_game_path(self):
        while True:
            game_path = diropenbox("Select Lethal Company folder")
            if game_path:
                shared_vars.set_game_path(game_path)
                break

    def get_mod_list(self):
        with open("mods.yml", "r", encoding="utf-8-sig") as file:
            data = yaml.safe_load(file)
        
        for mod in data:
            self.mod_list.append(Mod(mod["displayName"], mod["authorName"]))

    async def check_mods(self):
        console.app("Checking mods")

        semaphore = asyncio.Semaphore(5)
        tasks = []

        for mod in self.mod_list:
            async with semaphore:
                tasks.append(asyncio.create_task(mod.fetch_info()))

        await asyncio.gather(*tasks)

        for mod in self.mod_list:
            if not mod.is_updated:
                self.mods_to_download.append(mod)
        
        if self.mods_to_download.__len__() <= 0:
            console.info("Mods already up to date.")
            return
        
        console.info(f"Finished checking mods. ({self.mods_to_download.__len__()} mods to download)")

    async def handle_mods(self):
        console.app("Handling mods")
        semaphore = asyncio.Semaphore(5)
        tasks = []

        for mod in self.mods_to_download:
            console.downloading(mod.name, mod.latest_version)

            async with semaphore:
                tasks.append(asyncio.create_task(mod.download_mod()))

            await asyncio.gather(*tasks)

            tasks = []

            async with semaphore:
                tasks.append(asyncio.create_task(mod.install_mod()))

            await asyncio.gather(*tasks)
        
        console.info(f"Installed {self.mods_to_download.__len__()} mods.")

    def run(self):
        console.log(prefix=" ♕  LC-ModManager ", prefix_text_color=Fore.BLACK, prefix_back_color=Back.LIGHTMAGENTA_EX)

        self.get_game_path()

        os.makedirs(shared_vars.PLUGINS_FOLDER, exist_ok=True)
        os.makedirs(shared_vars.TEMP_FOLDER, exist_ok=True)

        self.get_mod_list()

        asyncio.run(self.check_mods())
        asyncio.run(self.handle_mods())

        shutil.rmtree(shared_vars.TEMP_FOLDER, ignore_errors=True)

        console.app("Finished")

def main():
    app = App()

    app.run()

if __name__ == "__main__":
    main()