import os
import subprocess
import shutil
import logging
from pathlib import Path
import requests
import json

class AudioTranslationEditor:
    """
    Class for managing audio translation operations.
    """

    bsarch_path: Path = None
    bmlfuzdecode_path: Path = None
    xwmaencode_path: Path = None
    is_initialized: bool = False
    xtts_url: str = None

    log = logging.getLogger("AudioTranslationEditor")

    def __init__(self, bsarch_path, bmlfuzdecode_path, xwmaencode_path, xtts_url):
        bsarch_path = Path(bsarch_path) if not isinstance(bsarch_path, Path) else bsarch_path
        bmlfuzdecode_path = Path(bmlfuzdecode_path) if not isinstance(bmlfuzdecode_path, Path) else bmlfuzdecode_path
        xwmaencode_path = Path(xwmaencode_path) if not isinstance(xwmaencode_path, Path) else xwmaencode_path

        self.bsarch_path = bsarch_path
        self.bmlfuzdecode_path = bmlfuzdecode_path
        self.xwmaencode_path = xwmaencode_path
        self.xtts_get_speakers_list = f'{xtts_url}/speakers_list'

        self.is_initialized = self.validate_paths() and self.check_if_xtts_is_running()
        
    def validate_paths(self) -> bool:
        if not self.bsarch_path.exists():
            self.log.error(f'BSArch path does not exist: {self.bsarch_path}')
            return False
        if not self.bmlfuzdecode_path.exists():
            self.log.error(f'BmlFuzDecode path does not exist: {self.bmlfuzdecode_path}')
            return False
        if not self.xwmaencode_path.exists():
            self.log.error(f'xWMAEncode path does not exist: {self.xwmaencode_path}')
            return False
        return True
    
    def check_if_xtts_is_running(self) -> bool:
        """
        Checks if the XTTS API server is running by querying the speakers list endpoint.

        Returns:
        bool: True if the server is running, else False.
        """
        try:
            response = requests.get(self.xtts_get_speakers_list)
            response.raise_for_status()
            return True
        except requests.exceptions.RequestException as e:
            self.log.error(f'Could not connect to XTTS API server: {e}')
            return False
        
    def extract_bsa(self, mod_path: Path) -> Path:
        """
        Extracts the BSA file in the given mod path, or if no BSA file is found,
        checks for .fuz or .xwm files and processes the directory containing them.

        Parameters:
        mod_path (Path): The path to the mod directory.

        Returns:
        Path: The path to the extracted files directory or the directory with .fuz/.xwm files.
        """
        # Ensure mod_path is a Path object
        mod_path = Path(mod_path) if not isinstance(mod_path, Path) else mod_path

        script_dir = Path(__file__).parent
        extract_destination = script_dir / 'extracted_files'

        # Remove the existing extracted_files directory if it exists
        if extract_destination.exists() and extract_destination.is_dir():
            shutil.rmtree(extract_destination)
            self.log.info(f'Removed existing directory: {extract_destination}')

        bsa_file = self.find_bsa_file(mod_path)
        if bsa_file:
            bsa_file_path = mod_path / bsa_file
            script_dir = Path(__file__).parent
            extract_destination = script_dir / 'extracted_files'
            extract_destination.mkdir(exist_ok=True)

            command = [str(self.bsarch_path), 'unpack', str(bsa_file_path), str(extract_destination)]

            try:
                subprocess.run(command, check=True)
                self.log.info(f'Successfully extracted {bsa_file} to {extract_destination}')
                return extract_destination
            except subprocess.CalledProcessError as e:
                self.log.error(f'An error occurred while extracting {bsa_file}: {e}')
                return None
        else:
            # Check for .fuz or .xwm files in the mod_path
            extracted_folder = self.find_audio_files(mod_path)
            if extracted_folder:
                self.log.info(f'Found .fuz or .xwm files in {extracted_folder}')
                return extracted_folder
            else:
                self.log.error(f'No .bsa or .fuz/.xwm files found in {mod_path}')
                return None

    def find_bsa_file(self, mod_path: Path) -> str:
        """
        Finds a .bsa file in the given mod path.

        Parameters:
        mod_path (Path): The path to the mod directory.

        Returns:
        str: The name of the .bsa file if found, else None.
        """
        for file in mod_path.iterdir():
            if file.suffix.lower() == '.bsa':
                return file.name
        return None

    def find_audio_files(self, mod_path: Path) -> Path:
        """
        Finds .fuz or .xwm files in the given mod path's directory tree.

        Parameters:
        mod_path (Path): The path to the mod directory.

        Returns:
        Path: The path to the directory containing .fuz or .xwm files, else None.
        """
        script_dir = Path(__file__).parent
        extract_destination = script_dir / 'extracted_files'
        extract_destination.mkdir(exist_ok=True)  # Ensure the extracted_files directory exists
        audio_files_path = None

        for root, _, files in os.walk(mod_path):
            for file in files:
                if file.lower().endswith(('.fuz', '.xwm')):
                    if audio_files_path is None:
                        audio_files_path = Path(root)
                    # Create directory structure in the destination path
                    destination_path = extract_destination / Path(root).relative_to(mod_path)
                    destination_path.mkdir(parents=True, exist_ok=True)
                    # Copy the file
                    shutil.copy(Path(root) / file, destination_path / file)
                    self.log.info(f'Copied {Path(root) / file} to {destination_path / file}')
        
        if audio_files_path:
            return extract_destination
        return None

    def convert_audio_files(self, extract_path: Path):
        """
        Converts .fuz and .xwm files to .wav and deletes unnecessary files.

        Parameters:
        extract_path (Path): The path to the directory with extracted files.
        """

        audio_files_found = False
        
        for subdir, _, files in os.walk(extract_path):
            for file in files:
                file_path = Path(subdir) / file
                if file_path.suffix.lower() == '.fuz':
                    self.decode_fuz(file_path)
                    audio_files_found = True                    
                elif file_path.suffix.lower() == '.xwm':
                    self.convert_xwm(file_path)
                    audio_files_found = True
                elif file_path.suffix.lower() == '.lip':
                    self.delete_file(file_path)
                    audio_files_found = True
        if audio_files_found:
            return True
        else:
            self.log.error(f'No .bsa or .fuz/.xwm files found in {extract_path}')
            return False

    def decode_fuz(self, file_path: Path):
        """
        Decodes a .fuz file to .xwm and converts it to .wav, then deletes the .fuz and .lip files.

        Parameters:
        file_path (Path): The path to the .fuz file.
        """
        decode_command = [str(self.bmlfuzdecode_path), str(file_path)]
        try:
            subprocess.run(decode_command, check=True)
            self.log.info(f'Successfully decoded {file_path} to .xwm')
        except subprocess.CalledProcessError as e:
            self.log.error(f'An error occurred while decoding {file_path}: {e}')
    
        # Convert .xwm to .wav if it exists
        xwm_file = file_path.with_suffix('.xwm')
        if xwm_file.exists():
            self.convert_xwm(xwm_file)
    
        # Delete the .fuz file
        self.delete_file(file_path)

        # Delete the corresponding .lip file if it exists
        lip_file = file_path.with_suffix('.lip')
        if lip_file.exists():
            self.delete_file(lip_file)

    def convert_xwm(self, file_path: Path):
        """
        Converts a .xwm file to .wav.

        Parameters:
        file_path (Path): The path to the .xwm file.
        """
        wav_file = file_path.with_suffix('.wav')
        convert_command = [str(self.xwmaencode_path), str(file_path), str(wav_file)]
        try:
            subprocess.run(convert_command, check=True)
            self.log.info(f'Successfully converted {file_path} to {wav_file}')
        except subprocess.CalledProcessError as e:
            self.log.error(f'An error occurred while converting {file_path} to {wav_file}: {e}')

        self.delete_file(file_path)

    def delete_file(self, file_path: Path):
        """
        Deletes a file.

        Parameters:
        file_path (Path): The path to the file to be deleted.
        """
        try:
            file_path.unlink()
            self.log.info(f'Deleted {file_path}')
        except OSError as e:
            self.log.error(f'An error occurred while deleting {file_path}: {e}')
