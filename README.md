# midiAuralizer
 This GUI allows to easily render MIDI- to Audiofiles through VST-Instruments and was developed for the Projects [DISKOS BMBF](https://organology.uni-leipzig.de/) and [MODAVIS (PhD)](https://modavis.org/){:target="\_blank"}.
 All parameters that have been set in the Instrument can be traced in a Protocol (JSON), including Hashcodes for every Audio- and MIDI-File to identify them for further management and processing. <br />
 <sub>Note: VST-Instruments only work on Windows, Support for Mac OS & Linux will be added soon (including Audio Units and SoundFonts)!</sub>

<p align="center">
  <img src="https://github.com/modavis-project/midiAuralizer/blob/main/images/midiAuralizer_screenshot0.PNG" alt="Screenshot of midiAuralizer's Main Window"/>
</p>

### Installation & Basic Usage (Windows)
 1. Download the <a href="https://github.com/modavis-project/midiAuralizer/releases" target="_blank">latest .zip-Archive</a>.
 2. Extract the Contents of the previously downloaded Archive to any Location.
 3. Start midiAuralizer.exe
 4. Set your VST- and Output-Folder and (optional) Audio-Parameters in Tools -> Preferences.
 5. Drag & Drop any MIDI-File or multiple MIDI-Files into the Main Window.
 6. Select the Instrument you want to use for the Auralization.
 7. (optional) Open the Instrument Window and change your Instrument Parameters.
 8. Click on Auralize MIDI - a Messagebox will confirm the successful Auralization and you can find the generated Audiofiles the Output-Folder that you've set before!
 9. If you want to check the used Instrument & Parameters of a generated Audiofile:
    - Open Tools -> Check Hashes
    - Drag & Drop your Audiofile into the Check Hashes - Window
 - If you encounter any Bugs, feel free to contact me!

### Features
 - Easy to Use: Simple GUI, no knowledge about Python or Digital Audio needed
 - Drag & Drop your MIDI-Files, choose your Instrument and click on Auralize !
 - Automatic Protocol: Instrument Parameters, Identifier & Hashcodes
 - Hashcode Checker: View Auralization Parameters for every generated Audiofile

### Upcoming Changes
 - Loading-Screen for App-Initialization and Instrument-Changes
 - Optimize State-Handling Operations
 - View & Export filtered Protocols
 - Progressbar for Batch Processing
 - Design Optimizations
 - Commandline-Version
 - Extend Support to Mac OS (Audio Units: .au) and SoundFonts (.sfz, .sf2)