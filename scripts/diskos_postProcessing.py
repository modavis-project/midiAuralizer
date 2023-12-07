"""
This script does the following:
1) Renaming of files to musiXplora Catalogus AURAL IDs depending on the defined parameters.
2) Conversion of all WAV files into MP3 files with 320kbps.
3) Translocation of all files (WAV & MP3) into directories based on their IDs.
4) Archiving the whole structure into a .zip file with the MP3 only for an mXp import.
"""

import os
import pandas as pd
from pathlib import Path
from pydub import AudioSegment
import zipfile

PROCESSING_DIR = 'C:/Users/Dominik/Desktop/GitProjects/midiAuralizer/output'

def rename_files():
    # Load the Excel file
    excel_path = 'C:/Users/Dominik/Desktop/Notenrollen 20231102.xlsx'  # Excel file path
    column_1 = 'Cat. SCAN'      # <-- Enter Input Column Name 1
    column_2 = 'Cat. MIDI'      # <-- Enter Input Column Name 2
    target_column = 'CAT AURAL' # <-- Enter Target Column (renames file to corresponding value in this column)
    
    print(f"Step 1: Renaming of files based on {excel_path} /nSearching in Columns '{column_1}' and '{column_2}'...")

    df = pd.read_excel(excel_path, sheet_name='MIDI').fillna(0)  # Excel sheet name

    # Define the directory containing the files
    directory_path = PROCESSING_DIR
    
    # List all files in the directory
    files_in_directory = os.listdir(directory_path)
    print(f'Found {len(files_in_directory)} files in the directory.')

    # Function to get the base name without extension
    def get_base_name(file_name):
        return os.path.splitext(file_name)[0]

    # Rename the files
    for file in files_in_directory:
        base_name = get_base_name(file)
        extension = os.path.splitext(file)[1]

        match_1 = df[df[column_1].astype(str) == base_name]
        match_2 = df[df[column_2].astype(int).astype(str) == base_name]

        if not match_1.empty:
            new_name = match_1[target_column].values[0]
            new_file_name = f'{new_name}{extension}'
            os.rename(os.path.join(directory_path, file), os.path.join(directory_path, new_file_name))
            print(f'Renamed "{file}" to "{new_file_name}".')
        elif not match_2.empty:
            new_name = match_2[target_column].values[0]
            new_file_name = f'{new_name}{extension}'
            os.rename(os.path.join(directory_path, file), os.path.join(directory_path, new_file_name))
            print(f'Renamed "{file}" to "{new_file_name}".')
        else:
            print(f'No match found for "{file}" in columns "{column_1}" and "{column_2}".')

def convert_to_mp3():
    print(f"Step 2: Converting WAV to MP3...")

    # Convert WAV to MP3
    for filename in os.listdir(PROCESSING_DIR):
        if filename.endswith(".wav"):
            wav_path = os.path.join(PROCESSING_DIR, filename)
            mp3_path = os.path.join(PROCESSING_DIR, filename.replace(".wav", ".mp3"))

            # Print the name of the file being processed
            print(f"Processing file: {filename}")

            # Load WAV file
            audio = AudioSegment.from_wav(wav_path)

            # Export as MP3 (320kbps, 2 Channels Stereo)
            audio.export(mp3_path, format="mp3", bitrate="320k", parameters=["-ac", "2"])

    # Print completion message
    print("Conversion complete. All WAV files have been converted to MP3.")

def move_into_directories():
    source_path = Path(PROCESSING_DIR)
    created_directories = set()

    print(f"Step 3: Moving WAV & MP3 files into ID directories...")

    for file in source_path.iterdir():
        if file.suffix in ['.mp3', '.wav']:
            file_id = file.stem.rsplit('_', 1)[0]
            target_dir = source_path / file_id
            if not target_dir.exists():
                created_directories.add(target_dir)
            target_dir.mkdir(exist_ok=True)
            file.rename(target_dir / file.name)

    # Writing the list of directories to a file
    with open(source_path / 'created_directories.txt', 'w') as f:
        for dir in sorted(created_directories):
            f.write(f"{dir}\n")

    print("Movement complete. All files have been moved to their corresponding ID directories.")

def zip_for_import():
    # Path to the output zip file
    zip_filename = "IMPORT_phonola_solodant.zip"
    zip_path = os.path.join(PROCESSING_DIR, zip_filename)

    print(f"Step 4: Creating .zip-Archive for musiXplora Import...")

    # Create a zip file
    with zipfile.ZipFile(zip_path, 'w') as zipf:
        # Walk through all directories and files in the parent directory
        for root, dirs, files in os.walk(PROCESSING_DIR):
            for file in files:
                # Check if the file is an MP3
                if file.endswith(".mp3"):
                    # Create the full file path
                    filepath = os.path.join(root, file)
                    # Create the arcname (path within the zip file)
                    arcname = os.path.relpath(filepath, PROCESSING_DIR)
                    # Add the file to the zip, maintaining its directory structure
                    zipf.write(filepath, arcname)

    print(f"Archiving complete, it can be found at {zip_path}")

if __name__ == "__main__":
    rename_files()
    convert_to_mp3()
    move_into_directories()
    zip_for_import()