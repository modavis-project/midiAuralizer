# midiAuralizer
 This GUI allows to easily render MIDI- to Audiofiles through VST-Instruments and was developed for the Projects [DISKOS (BMBF)](https://organology.uni-leipzig.de/) and [MODAVIS (PhD)](https://modavis.org/).
 All parameters that have been set in the Instrument can be traced in a Protocol (JSON), including Hashcodes for every Audio- and MIDI-File to identify them for further management and processing. <br />
 <sub>Note: VST-Instruments only work on Windows, Support for Mac OS & Linux will be added soon (including Audio Units and SoundFonts)!</sub>

<p align="center">
  <img src="https://github.com/modavis-project/midiAuralizer/blob/main/images/midiAuralizer_screenshot0.PNG" alt="Screenshot of midiAuralizer's Main Window"/>
</p>

### Features
 - Easy to Use: Simple GUI, no programming or digital audio knowledge needed
 - Drag & Drop your MIDI-Files, choose your Instrument and click on Auralize !
 - Automatic Protocol: Instrument Parameters, Identifier & Hashcodes
 - Hashcode Checker: View Auralization Parameters for every generated Audiofile

### Upcoming Changes
 - Loading-Screen for App-Initialization and Instrument-Changes
 - Optimize State-Handling Operations
 - View & Export filtered Protocols
 - Progressbar for Batch Processing
 - Commandline-Version
 - Extend Support to Mac OS (Audio Units: .au) and SoundFonts (.sfz, .sf2)