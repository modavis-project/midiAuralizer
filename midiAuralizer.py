# -*- coding: utf-8 -*-
"""
Created on Thu Aug  11 13:25:43 2022

@author: Dominik Ukolov
@email: dominik.ukolov@uni-leipzig.de
@site: https://modavis.org/
@description: This Tool has been developed for the Projects DISKOS (BMBF) and MODAVIS (PhD) to execute quick auralizations with traceable parameters and identifiers for virtual instruments and the corresponding MIDI- & Audio-Files.
"""

from PyQt5.QtWidgets import (QLabel, QComboBox, QLineEdit, QPushButton, QFrame, QMainWindow, 
                             QDialog, QApplication, QWidget, QMenuBar, QMenu, QAction, QStatusBar, 
                             QGridLayout, QDialogButtonBox, QFormLayout, QCheckBox, QFileDialog, QMessageBox)
from PyQt5.QtGui import QPixmap, QIntValidator, QDesktopServices, QIcon
from PyQt5.QtCore import Qt
from PyQt5 import QtCore
import sys
import json
import os
from datetime import datetime
import mido
import hashlib
from win32api import GetFileVersionInfo, LOWORD, HIWORD
import dawdreamer as daw
from scipy.io import wavfile

win_x = 300
win_y = 300
win_width = 520
win_height = 400

cwd = os.getcwd()
cwd_css = cwd.replace("\\", "/")
userpath = os.environ['USERPROFILE']
SETTINGS_PATH = f"{cwd}\\db\\settings.json"
PROTOCOL_PATH = f"{cwd}\\db\\protocol.json"

def initResources(): # creates predefined .json-Files and folder structure if unavailable
    settings = {"audioSettings": {"samplerate": 44100, "bitdepth": 16, "chunksize": 1024, "loadstate": True},
     "pathSettings": {"vstpath": "C:\\VstPlugins\\", "outpath": f"{cwd}\\output\\", "statespath": f"{cwd}\\states\\"},
     "pluginSettings": {}}
    protocol = {}
    for i in [f"{cwd}\\output\\", f"{cwd}\\states\\", f"{cwd}\\db\\"]:
        if not os.path.exists(i):
            os.mkdir(i)
    if not os.path.exists(SETTINGS_PATH):
        with open(SETTINGS_PATH, "w") as settings_file:
            json.dump(settings, settings_file, indent=4)
        settings_file.close()
    if not os.path.exists(PROTOCOL_PATH):
        with open(PROTOCOL_PATH, "w") as protocol_file:
            json.dump(protocol, protocol_file, indent=4)
        protocol_file.close()

initResources()

json_settings = json.load(open(SETTINGS_PATH, encoding='UTF-8'))
json_protocol = json.load(open(PROTOCOL_PATH, encoding='UTF-8'))

VST_PATH = json_settings['pathSettings']['vstpath']
OUT_PATH = json_settings['pathSettings']['outpath']
STATES_PATH = json_settings['pathSettings']['statespath']
BACKGROUND_MAIN = f"{cwd_css}/images/bgImage.png"
ICON_PATH = f"{cwd}\\images\\icon.png"
RESOURCES = [f"{cwd}\\images\\bgImage.png", f"{cwd}\\images\\MIDI_Drag.png", f"{cwd}\\images\\Audio_Drag.png", f"{cwd}\\images\\DropDownArrow.png",
             ICON_PATH, SETTINGS_PATH, PROTOCOL_PATH]

SAMPLERATE = int(json_settings['audioSettings']['samplerate'])
tempo = 230
BIT_DEPTH = int(json_settings['audioSettings']['bitdepth'])
CHUNKSIZE = int(json_settings['audioSettings']['chunksize'])
LOAD_STATE = bool(json_settings['audioSettings']['loadstate'])

instrument = None
parameters = ""
dict_parameters = {}

def jsonDump(json_target): # dumps data into target json file
    if json_target == "settings": 
        with open(SETTINGS_PATH, "w") as json_file:
            json.dump(json_settings, json_file, indent=4)
        json_file.close()
    elif json_target == "protocol":
        with open(PROTOCOL_PATH, "w") as json_file:
            json.dump(json_protocol, json_file, indent=4)
        json_file.close()
    else:
        print("JSON-Target not found.")
        
def getHashes(audiofile, midifile): # returns hashcodes for the corresponding audio- and midifiles
    path_audio = audiofile
    blocksize = 65536
    hash_audio = hashlib.md5()
    with open(path_audio, "rb") as file_audio:
        fb = file_audio.read(blocksize)
        while len(fb) > 0:
            hash_audio.update(fb)
            fb = file_audio.read(blocksize)
    hash_audio = hash_audio.hexdigest()
    file_audio.close()
    
    hash_midi = hashlib.md5()
    with open(path_audio, "rb") as file_midi:
        fb = file_midi.read(blocksize)
        while len(fb) > 0:
            hash_midi.update(fb)
            fb = file_midi.read(blocksize)
    hash_midi = hash_midi.hexdigest()
    file_midi.close()
    return [hash_audio, hash_midi]

def getPluginVersion(instrument): # gets plugin version from the VSTs .dll-File
    info = GetFileVersionInfo(f"{VST_PATH}{instrument}.dll", "\\")
    ms = info['FileVersionMS']
    ls = info['FileVersionLS']
    version = f"{HIWORD (ms)}.{LOWORD (ms)}.{HIWORD (ls)}.{LOWORD (ls)}"
    return version

def Start(): # starts the Application
    global mwin
    mwin = Main()
    mwin.setGeometry(win_x, win_y, win_width, win_height)
    mwin.show()
    return mwin
        
class Main(QMainWindow):
    auralized_files = []
    current_midifiles = []
    def __init__(self, parent=None):
        global instrument
        super(Main, self).__init__(parent)
        self.setWindowTitle("midiAuralizer")
        self.setFixedSize(win_width, win_height)
        self.setWindowIcon(QIcon(ICON_PATH))
        self.centralWidget = QWidget(self)

        self.checkResources()        
        self.createMenuBar()
        self.createStatusBar()
        
        self.setCentralWidget(self.centralWidget)
        self.layout = QGridLayout(self.centralWidget)
        
        self.list_instruments = []
        for i in os.listdir(VST_PATH):
            if i[-4:] == '.dll':
                self.list_instruments.append(i[:-4])
        
        self.midifiles = []
        self.img_dragMidi = QLabel(self)
        self.img_dragMidi.setPixmap(QPixmap(f"{cwd_css}/images/MIDI_Drag.png"))
        self.img_dragMidi.mousePressEvent = self.clickLoadMIDI
        self.img_dragMidi.setFixedSize(500, 140)
        self.setAcceptDrops(True)
        
        self.lbl_instrument = QLabel("Instrument")
        self.combo_instruments = QComboBox()
        self.combo_instruments.addItems(self.list_instruments)
        instrument = self.combo_instruments.currentText()
        self.combo_instruments.currentIndexChanged.connect(self.injectInstrumentChoice)
        if LOAD_STATE == True:
            self.combo_instruments.currentIndexChanged.connect(self.setLastParameters)
        self.combo_instruments.setStyleSheet(style_mainCombo)
        
        self.btInstrumentSettings = QPushButton("Instrument Settings")
        self.btInstrumentSettings.clicked.connect(self.openPlugin)
        self.btInstrumentSettings.setFixedSize(250, 40)
        self.btInstrumentSettings.setStyleSheet(style_mainBt)
        
        self.btAuralize = QPushButton("Auralize MIDI")
        self.btAuralize.clicked.connect(self.Auralize)
        self.btAuralize.setFixedSize(250, 40)
        self.btAuralize.setStyleSheet(style_mainBt)
        
        validatorINT = QIntValidator()
        self.lbl_tempo = QLabel("Tempo (BPM)")
        self.lbl_tempo.setAlignment(Qt.AlignCenter)
        self.lbl_tempo.setStyleSheet("color: mintcream; border: 1px solid #424c5c; border-radius: 4px; margin: 12px 10px 0px 0px;")
        self.val_tempo = QLineEdit()
        self.val_tempo.setValidator(validatorINT)
        self.val_tempo.setStyleSheet("background-color: #424c5c; color: mintcream; padding-left: 6px; max-width: 35; margin: 10px 0px 0px 0px; border: 1px solid black; border-radius: 4px;")
        self.val_tempo.setText(str(tempo))
        
        self.layout.addWidget(self.img_dragMidi, 0, 0, 1, 100, alignment=Qt.AlignTop)
        self.layout.addWidget(self.combo_instruments, 2, 0, 1, 100, alignment=Qt.AlignTop)
        self.layout.addWidget(self.btInstrumentSettings, 3, 3, 1, 40, alignment=Qt.AlignTop)
        self.layout.addWidget(self.btAuralize, 3, 53, 1, 40, alignment=Qt.AlignTop)
        self.layout.addWidget(self.lbl_tempo, 4, 27, 1, 20, alignment=Qt.AlignTop)
        self.layout.addWidget(self.val_tempo, 4, 44, 1, 20, alignment=Qt.AlignTop)
        
        self.layout.setSpacing(10)
        
        self.engine = daw.RenderEngine(SAMPLERATE, CHUNKSIZE)
        self.loadInstrument()
        
    def checkResources(self): # checks if all Resources are located at the right path
        missing_resources = []
        for i in RESOURCES:
            if not os.path.exists(i):
                missing_resources.append(i)
        
        if missing_resources:
            self.errorNoResources(missing_resources)
                
    def errorNoResources(self, missing_resources):
        str_missing_resources = ""
        for i in missing_resources:
            str_missing_resources += f"{i}\n"
        errorBox = QMessageBox(QMessageBox.Question, "Missing Resources", 
                               f"Resource Files could not be found! Please place them in the some folder as this executable and relaunch the App.\n\nMissing Resources: \n\n{str_missing_resources}", 
                               QMessageBox.No)
        errorBox.button(QMessageBox.No).setText("Okay")
        errorBox.exec_()
                
    def errorNoInstruments(self): # gives an Error if there aren't any VSTs in the specified path
        errorBox = QMessageBox(QMessageBox.Question, "No VST Found!", 
                               "No Instruments found in VST-Path! Please select another Path where your VST-Files are located.", 
                               QMessageBox.Yes | QMessageBox.No)
        errorBox.button(QMessageBox.Yes).setText("Select VST Folder")
        answer = errorBox.exec_()
        
        if answer == QMessageBox.Yes:
            self.loadPathVST()
            self.refreshInstrumentsList()
        else:
            self.printStatus("WARNING: No VST found. Please specify a Path in the Preferences!")
            
    def createMenuBar(self): # creates the Menubar
        menuBar = QMenuBar(self)
        mainMenu = QMenu("Operations", self)
        menuBar.addMenu(mainMenu)
        toolsMenu = QMenu("Tools", self)
        menuBar.addMenu(toolsMenu)
        self.setMenuBar(menuBar)
        
        self.loadAction = QAction("Load MIDI", self)
        self.exeAction = QAction("Auralize MIDI", self)
        
        self.exitAction = QAction("Exit", self)
        self.loadAction.triggered.connect(self.loadMIDI)
        self.exeAction.triggered.connect(self.Auralize)
        
        self.exitAction.triggered.connect(self.quitApp)
        mainMenu.addAction(self.loadAction)
        mainMenu.addAction(self.exeAction)
        mainMenu.addAction(self.exitAction)
        self.preferencesAction = QAction("Preferences")
        self.preferencesAction.triggered.connect(self.openPreferences)
        self.listMidisAction = QAction("List MIDI-Files", self)
        self.listMidisAction.triggered.connect(self.openListMidis)
        self.hashesAction = QAction("Check Hashes", self)
        self.hashesAction.triggered.connect(self.openCheckHashes)
        self.aboutAction = QAction("About", self)
        self.aboutAction.triggered.connect(self.openAbout)
        toolsMenu.addAction(self.preferencesAction)
        toolsMenu.addAction(self.listMidisAction)
        toolsMenu.addAction(self.hashesAction)
        toolsMenu.addAction(self.aboutAction)
        
    def createStatusBar(self): # creates statusbar
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        
    def printStatus(self, status_msg, timer=10000): # print to StatusBar, timer defines the duration of the message in ms
        self.statusBar.showMessage(status_msg, timer)
        # to activate through Button etc.: self.button.triggered.connect(partial(self.printStatus, "Button Clicked"))

    def refreshInstrumentsList(self): # reloads the Instruments List, e.g. after changing the VST-Path in Preferences
        global instrument
        self.list_instruments = []
        for i in os.listdir(VST_PATH):
            if i[-4:] == '.dll':
                self.list_instruments.append(i[:-4])
        self.combo_instruments.addItems(self.list_instruments)
        instrument = self.combo_instruments.currentText()
        self.loadInstrument()
    
    def loadInstrument(self): # loads an Instrument into the engine
        try:
            self.synth = self.engine.make_plugin_processor(instrument, VST_PATH + instrument + ".dll")
            if LOAD_STATE == True:
                self.setLastParameters()
            self.printStatus("App initiated successfully.")
        except RuntimeError as e:
            if str(e) == 'Unable to load plugin.':
                self.errorNoInstruments()
            else:
                print(f"Error: {str(e)}")
        
    def loadPathVST(self): # opens a File Dialog to choose a new VST Path and dump it in the Settings
        global VST_PATH
        path = QFileDialog.getExistingDirectory(self, "Choose VST Directory")
        if path:
            VST_PATH = (path+"/").replace("/", "\\")
            json_settings['pathSettings']['vstpath'] = VST_PATH
            jsonDump("settings")
        else:
            self.errorNoInstruments()
            
    def injectInstrumentChoice(self): # changes current instrument
        global instrument
        instrument = self.combo_instruments.currentText()
        self.printStatus("Loading Instrument...", timer=3000)
        self.synth = self.engine.make_plugin_processor(instrument, VST_PATH + instrument + ".dll")
        self.printStatus(f"Instrument {instrument} successfully loaded!")
            
    def setLastParameters(self): # load last parameters for selected instrument, this can be set optional in settings
        if LOAD_STATE == True:
            if instrument in json_settings['pluginSettings']:
                for i in range(0, len(json_settings['pluginSettings'][instrument])):
                    paramName = self.synth.get_parameter_name(i)
                    self.synth.set_parameter(i, json_settings['pluginSettings'][instrument][paramName])
        
    def dragEnterEvent(self, event): # checks if dragged data are files
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event): # puts dropped files into midifiles-list
        self.midifiles = []
        for url in event.mimeData().urls():
            self.midifiles.append(url.toLocalFile())
        if len(self.midifiles) > 1:
            self.printStatus("Multiple MIDI-Files successfully loaded!")
        elif len(self.midifiles) == 1:
            self.printStatus(f"MIDI-File: <{os.path.basename(self.midifiles[0])}> successfully loaded!")
        if not self.midifiles:
            self.printStatus("No MIDI-File selected.")
        
    def clickLoadMIDI(self, event): # click event for midi drag & drop field
        self.loadMIDI()
        
    def loadMIDI(self): # loads MIDI-Files via File Dialog
        self.midifiles = []
        Main.current_midifiles = []
        midi_fnames = QFileDialog.getOpenFileNames(self, 'Open MIDI File', cwd, "MIDI-File (*.mid)")
        for i in midi_fnames[0]:
            self.midifiles.append(i)
            Main.current_midifiles.append(i)
        if len(self.midifiles) > 1:
            self.printStatus("Multiple MIDI-Files successfully loaded!")
        elif len(self.midifiles) == 1:
            self.printStatus(f"MIDI-File: <{os.path.basename(self.midifiles[0])}> successfully loaded!")
        if not self.midifiles:
            self.printStatus("No MIDI-File selected.")
            
    def setTempo(self, midi, tempo): # sets Tempo of current MIDI-File & saves temporary version for processing
        midi_pathdata = os.path.split(midi)
        mid = mido.MidiFile(midi)
        new_mid = mido.MidiFile()
        new_track = mido.MidiTrack()
        new_mid.tracks.append(new_track)
        for i, track in enumerate(mid.tracks):
            for msg in track:
                if msg.type == 'set_tempo':
                    new_tempo = int(mido.bpm2tempo(tempo))
                    msg.tempo = new_tempo
                new_track.append(msg)
        new_mid.save(f"{midi_pathdata[0]}\\{midi_pathdata[1][:-4]}_temp.mid")
            
    def Auralize(self): # starts Auralization process and saves hash codes of generated files into .json
        global instrument, dict_parameters, json_settings, json_protocol
        if not self.midifiles:
            errorBox = QMessageBox()
            errorBox.setIcon(QMessageBox.Critical)
            errorBox.setText("No MIDI-File loaded. Please select a MIDI-File!")
            errorBox.exec_()
            return
        Main.auralized_files = []
        instrument = self.combo_instruments.currentText()
        assert self.synth.get_name() == instrument
        tempo = int(self.val_tempo.text())
        
        filesize_threshold = 500 # threshold in bytes for checking the successful processing (simple)
        
        if instrument in json_settings['pluginSettings']:
            dict_parameters = json_settings['pluginSettings'][instrument]
        else:
            json_settings['pluginSettings'][instrument] = self.getPluginParameters()
            jsonDump("settings")
            dict_parameters = json_settings['pluginSettings'][instrument]
            
        plugin_version = getPluginVersion(instrument)
        json_settings['audioSettings']['samplerate'] = str(SAMPLERATE)
        json_settings['audioSettings']['bitdepth'] = str(BIT_DEPTH)
        jsonDump("settings")
        
        if not self.midifiles:
            self.printStatus("No MIDI-File selected for Auralization.")
        for midi in self.midifiles:
            self.setTempo(midi, tempo)
            midipath = midi[:-4] + "_temp.mid"
            outpath = f'{OUT_PATH}{os.path.basename(midipath.replace("_temp.mid", ""))}.wav'
            self.synth.load_midi(midipath, clear_previous=True, beats=False, all_events=True)
            graph = [(self.synth, [])]
            self.engine.load_graph(graph)
            midi_endtime = mido.MidiFile(midipath).length
            self.renderAudio(engine=self.engine, file_path=outpath, duration=midi_endtime+5.)
            timestamp = datetime.now()
            
            if os.path.exists(outpath):
                if os.path.getsize(outpath) > filesize_threshold:
                    Main.auralized_files.append(outpath)
                    
                    hashes = getHashes(audiofile=outpath, midifile=midipath)
                    hash_audio = str(hashes[0])
                    hash_midi = str(hashes[1])
                    
                    json_protocol[hash_audio] = {
                        "filename": os.path.basename(outpath), 
                        "created": str(timestamp), 
                        "samplerate": str(SAMPLERATE), 
                        "bitdepth": str(BIT_DEPTH),
                        "midi": {
                            "filename": os.path.basename(midipath.replace("_temp", "")),
                            "tempo": tempo,
                            "hash": hash_midi
                            },
                        "tempo": str(tempo),
                        "plugin": {
                            "name": str(instrument),
                            "version": plugin_version,
                            "parameters": dict_parameters}
                        }
                    jsonDump("protocol")
                else:
                    self.printStatus(f"Output-File {os.path.basename(outpath)} seems to be corrupted or empty.")
            else:
                self.printStatus("Output File has not been created. Auralization failed!")
            if os.path.isfile(midipath):
                os.remove(midipath)
        
        if os.path.exists(outpath):
            if os.path.getsize(outpath) > filesize_threshold:
                self.printStatus(f"Auralization on {instrument} successful!")
                self.openResults()
        else:
            self.printStatus(f"Auralization on {instrument} probably failed, please check the Output-Files.")
        
    def renderAudio(self, engine, file_path, duration): # renders Audio to .wav
    	assert(self.engine.render(duration))
    	audio_output = self.engine.get_audio()
    	if file_path is not None:
    		wavfile.write(file_path, SAMPLERATE, audio_output.transpose())
            
    def getPluginParameters(self): # returns plugin parameters
        params_length = self.synth.get_plugin_parameter_size()
        decoded_parameters = {}
        for i in range(0, params_length):
            paramName = self.synth.get_parameter_name(i)
            decoded_parameters[paramName] = self.synth.get_parameter(i)
        return decoded_parameters    
        
    def openResults(self): # opens window with auralization results
        dlg_results = Results()
        if dlg_results.exec():
            QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(OUT_PATH))
            
    def openListMidis(self): # opens window with currently loaded MIDI-Files
        dlg_listMidis = ListMidis()
        if dlg_listMidis.exec():
            self.printStatus("List of MIDI-Files closed.")
        
    def openCheckHashes(self): # opens window to check auralization parameters through audio hashes
        dlg_instrument = CheckHashes()
        if dlg_instrument.exec():
            self.printStatus("Hashes Checked.")
            
    def openPreferences(self): # opens preferences window
        dlg_preferences = Preferences()
        
        if dlg_preferences.exec():
            self.printStatus("Preferences saved!")
            if LOAD_STATE == True:
                self.combo_instruments.currentIndexChanged.connect(self.setLastParameters)
            else:
                self.combo_instruments.currentIndexChanged.disconnect(self.setLastParameters)
            self.refreshInstrumentsList()
        else:
            self.printStatus("Preferences closed without saving.")
            
    def openAbout(self):
        dlg_about = About()
        dlg_about.exec()
            
    def openPlugin(self): # opens vst window and saves changed parameters
        self.synth.open_editor()
        statenum = 1
        savestate_path = f'{userpath}\\OneDrive\\2022\\Scripts\\midi_to_mp3\\states\\{instrument}\\state{statenum}'
        initial_save = False
        if os.path.exists(f'{userpath}\\OneDrive\\2022\\Scripts\\midi_to_mp3\\states\\{instrument}\\') == False:
            os.mkdir(f'{userpath}\\OneDrive\\2022\\Scripts\\midi_to_mp3\\states\\{instrument}\\')
            self.synth.save_state(f'{userpath}\\OneDrive\\2022\\Scripts\\midi_to_mp3\\states\\{instrument}\\state0')
            initial_save = True
        
        if initial_save == False:
            while os.path.exists(f'{userpath}\\OneDrive\\2022\\Scripts\\midi_to_mp3\\states\\{instrument}\\state{statenum}') == True:
                statenum += 1
                savestate_path = f'{userpath}\\OneDrive\\2022\\Scripts\\midi_to_mp3\\states\\{instrument}\\state{statenum}'
            self.synth.save_state(savestate_path)
        
        dict_parameters = self.getPluginParameters()
        json_settings['pluginSettings'][instrument] = dict_parameters
        jsonDump("settings")
        self.printStatus("Instrument Status has been saved for Auralization!")
        
    def quitApp(self): # quits App
        mwin.close()
        
class ListMidis(QDialog): # window which includes currently loaded MIDIs
    def __init__(self):
        super().__init__()
        self.setWindowTitle("List of currently loaded MIDI-Files")
        self.setWindowIcon(QIcon(ICON_PATH))
        buttons = QDialogButtonBox.Ok
        self.buttonBox = QDialogButtonBox(buttons)
        self.buttonBox.button(QDialogButtonBox.Ok).setText("Close")
        self.buttonBox.accepted.connect(self.accept)
        
        self.layout = QFormLayout()
        self.setLayout(self.layout)
        
        self.lbl_msg = QLabel(self)
        
        midis = Main.current_midifiles
        
        if midis:
            self.lbl_msg.setText("The following MIDI-Files are currently loaded: ")
        else:
            self.lbl_msg.setText("No MIDI-Files are currently loaded.")
            
        self.layout.addRow(self.lbl_msg)
        
        
        
        for i in range(0, len(midis)):
            lbl_text = midis[i].replace("\\", "/")
            exec(
f"""
self.lbl_midis{i} = QLabel("{lbl_text}")
self.layout.addRow(self.lbl_midis{i})
""")
        
        self.layout.addRow(self.buttonBox)
        
class Results(QDialog): # window with a list of all successfully auralized files (full path)
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Auralization Results")
        self.setWindowIcon(QIcon(ICON_PATH))
        buttons = QDialogButtonBox.Open | QDialogButtonBox.Close
        self.buttonBox = QDialogButtonBox(buttons)
        self.buttonBox.button(QDialogButtonBox.Open).setText("Open Containing Folder")
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        self.layout = QFormLayout()
        self.setLayout(self.layout)
        
        self.lbl_msg = QLabel("Auralization successful! The following files have been rendered: ")
        self.layout.addRow(self.lbl_msg)
        
        auralized = Main.auralized_files
        
        for i in range(0, len(auralized)):
            lbl_text = auralized[i].replace("\\", "/")
            exec(
f"""
self.lbl_results{i} = QLabel("{lbl_text}")
self.layout.addRow(self.lbl_results{i})
""")
        
        self.layout.addRow(self.buttonBox)
        
class Preferences(QDialog): # preferences window
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Preferences")
        self.setWindowIcon(QIcon(ICON_PATH))
        self.setFixedWidth(550)
        buttons = QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        self.buttonBox = QDialogButtonBox(buttons)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.accepted.connect(self.savePreferences)
        self.buttonBox.rejected.connect(self.reject)
        
        self.layout = QFormLayout()
        self.setLayout(self.layout)
        
        self.lbl_vstpath = QLabel("VSTi Path")
        self.val_vstpath = PathEdit(doubleClicked=self.on_doubleClicked)
        self.val_vstpath.setText(VST_PATH)
        self.val_vstpath.setToolTip("Double-Click to choose another VSTi-Path")
        self.lbl_outpath = QLabel("Output Path")
        self.val_outpath = PathEdit(doubleClicked=self.on_doubleClicked)
        self.val_outpath.setText(OUT_PATH)
        self.val_outpath.setToolTip("Double-Click to choose another Output-Path")
        self.lbl_statespath = QLabel("Instrument States Path")
        self.val_statespath = PathEdit(doubleClicked=self.on_doubleClicked)
        self.val_statespath.setText(STATES_PATH)
        self.val_statespath.setToolTip("Double-Click to choose another States-Path")
        
        self.dict_samplerates = {'44100': 0, '48000': 1, '96000': 2, '192000': 3, '384000': 4}
        self.lbl_samplerate = QLabel("Samplerate")
        self.lbl_samplerate.setAlignment(Qt.AlignCenter)
        self.combo_samplerates = QComboBox()
        self.combo_samplerates.addItems(list(self.dict_samplerates.keys()))
        self.combo_samplerates.setCurrentIndex(self.dict_samplerates[str(SAMPLERATE)])
        self.dict_bitdepths = {'8': 0, '16': 1, '24': 2, '32': 3}
        self.lbl_bitdepth = QLabel("Bit Depth")
        self.lbl_bitdepth.setAlignment(Qt.AlignCenter)
        self.combo_bitdepths = QComboBox()
        self.combo_bitdepths.addItems(list(self.dict_bitdepths.keys()))
        self.combo_bitdepths.setCurrentIndex(self.dict_bitdepths[str(BIT_DEPTH)])
        self.combo_samplerates.setStyleSheet("padding-left: 3px;")
        self.combo_bitdepths.setStyleSheet("padding-left: 3px;")
        
        self.lbl_chunksize = QLabel("Chunksize")
        self.val_chunksize = QLineEdit(str(CHUNKSIZE))
        self.intValidator = QIntValidator()
        self.val_chunksize.setValidator(self.intValidator)
        self.lbl_loadstate = QLabel("Load last Instrument-State")
        self.cb_loadstate = QCheckBox(self)
        self.cb_loadstate.setChecked(LOAD_STATE)
        
        self.lbl_empty = QLabel("")
        
        self.layout.setSpacing(13)
        
        self.layout.addRow(self.lbl_vstpath, self.val_vstpath)
        self.layout.addRow(self.lbl_outpath, self.val_outpath)
        self.layout.addRow(self.lbl_statespath, self.val_statespath)
        self.layout.addRow(self.lbl_samplerate, self.combo_samplerates)
        self.layout.addRow(self.lbl_bitdepth, self.combo_bitdepths)
        self.layout.addRow(self.lbl_chunksize, self.val_chunksize)
        self.layout.addRow(self.lbl_loadstate, self.cb_loadstate)
        self.layout.addRow(self.lbl_empty)
        self.layout.addRow(self.buttonBox)
        
    @QtCore.pyqtSlot()
    def on_doubleClicked(self):
        global path
        if self.sender() is self.val_vstpath:
            path = QFileDialog.getExistingDirectory(self, "Choose VST Directory")
            if path:
                self.val_vstpath.setText(path.replace("/", "\\") + "\\")
        elif self.sender() is self.val_outpath:
            path = QFileDialog.getExistingDirectory(self, "Choose Output Directory")
            if path:
                self.val_outpath.setText(path.replace("/", "\\") + "\\")
        elif self.sender() is self.val_statespath:
            path = QFileDialog.getExistingDirectory(self, "Choose Instrument States Directory")
            if path:
                self.val_statespath.setText(path.replace("/", "\\") + "\\")
        
    def savePreferences(self):
        global SAMPLERATE, VST_PATH, OUT_PATH, BIT_DEPTH, CHUNKSIZE, LOAD_STATE, STATES_PATH
        VST_PATH = self.val_vstpath.text()
        OUT_PATH = self.val_outpath.text()
        STATES_PATH = self.val_statespath.text()
        SAMPLERATE = int(self.combo_samplerates.currentText())
        BIT_DEPTH = int(self.combo_bitdepths.currentText())
        CHUNKSIZE = int(self.val_chunksize.text())
        LOAD_STATE = bool(self.cb_loadstate.isChecked())
        
        json_settings['pathSettings']['vstpath'] = VST_PATH
        json_settings['pathSettings']['outpath'] = OUT_PATH
        json_settings['pathSettings']['statespath'] = STATES_PATH
        json_settings['audioSettings']['samplerate'] = SAMPLERATE
        json_settings['audioSettings']['bitdepth'] = BIT_DEPTH
        json_settings['audioSettings']['chunksize'] = CHUNKSIZE
        json_settings['audioSettings']['loadstate'] = LOAD_STATE
        jsonDump("settings")
            
class CheckHashes(QDialog): # window to check protocol/parameters by generated hashes 
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Check Hashes")
        self.setWindowIcon(QIcon(ICON_PATH))
        buttons = QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        self.buttonBox = QDialogButtonBox(buttons)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        
        self.layout = QFormLayout()
        self.setLayout(self.layout)
        
        self.img_dragAudio = QLabel(self)
        self.img_dragAudio.setPixmap(QPixmap(f"{cwd_css}/images/Audio_Drag.png"))
        self.img_dragAudio.mousePressEvent = self.clickLoadAudio
        self.img_dragAudio.setFixedSize(500, 140)
        self.setAcceptDrops(True)
        
        self.layout.addRow(self.img_dragAudio)
        
        self.loaded = False
        self.tmp_elements = []
        
    def dragEnterEvent(self, event): # same as in Main class
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event): # creates info after dropping audiofile
        lines = []
        for url in event.mimeData().urls():
            lines.append(url.toLocalFile())
        self.audiopath = url.toLocalFile()
        audiohash = self.getHash()
        self.genInfo(self.audiopath, audiohash)
        
    def clickLoadAudio(self, event): # executes selectAudioFile-Function after click in the drag & drop field
        self.selectAudioFile()
        
    def selectAudioFile(self): # opens file dialog to select audiofile
        self.audiopath = QFileDialog.getOpenFileName(self, 'Open Audiofile', cwd, "Audiofile (*.wav)")[0]
        if self.audiopath:
            #self.layout.addRow(QLabel("Audio Filepath: "), QLabel(self.audiopath))
            audiohash = self.getHash()
            self.genInfo(self.audiopath, audiohash)
        
    def getHash(self): # called in genInfo: creates parameter infos and sets them in current window
        blocksize = 65536
        hash_audio = hashlib.md5()
        with open(self.audiopath, "rb") as file_audio:
            fb = file_audio.read(blocksize)
            while len(fb) > 0:
                hash_audio.update(fb)
                fb = file_audio.read(blocksize)
        return str(hash_audio.hexdigest())
    
    def genParamInfo(self, val_text):
        if self.tmp_elements:
            for i in self.tmp_elements:
                eval(f'{i}.deleteLater()')
        self.tmp_elements = []
        
        for j in range(0, len(list(val_text))):
            exec(
f'''
lbl_a_text = str(list(val_text)[j])
val_a_text = str(list(val_text.values())[j])
self.lbl_a{j} = QLabel(self)
self.lbl_a{j}.setAlignment(Qt.AlignLeft)
self.lbl_a{j}.setText(lbl_a_text)
self.val_a{j} = QLabel(self)
self.val_a{j}.setAlignment(Qt.AlignLeft)
self.val_a{j}.setText(val_a_text)
self.val_a{j}.setTextInteractionFlags(Qt.TextSelectableByMouse)
self.layout.addRow(self.lbl_a{j}, self.val_a{j})
self.tmp_elements.append('self.lbl_a{j}')
self.tmp_elements.append('self.val_a{j}')
''')
        
    def genInfo(self, audiopath, audiohash): # generates file info and sets/replaces them in current window
        try:
            entry = json_protocol[audiohash]
            outdict = {
                "Audio Filepath: ": str(audiopath),
                "Audio Hashcode: ": str(audiohash),
                "Original Filename: ": entry['filename'],
                "Date of Creation: ": entry['created'],
                "Original Samplerate: ": entry['samplerate'],
                "Original Bit Depth: ": entry['bitdepth'],
                "MIDI for Auralization: ": entry['midi']['filename'],
                "MIDI Hashcode: ": entry['midi']['hash'],
                "BPM of Rendering: ": entry['tempo'],
                "Plugin: ": entry['plugin']['name'],
                "Plugin Ver.: ": entry['plugin']['version'],
                "Plugin Parameters: ": entry['plugin']['parameters']
                }
            
            for i in range(0, len(list(outdict))):
                exec(
f'''
lbl_text = str(list(outdict)[{i}])
val_text = list(outdict.values())[{i}]
if self.loaded == False:
    self.lbl{i} = QLabel(self)
    self.lbl{i}.setAlignment(Qt.AlignLeft)
    self.lbl{i}.setText(lbl_text)
    if type(val_text) != dict:
        self.val{i} = QLabel(self)
        self.val{i}.setAlignment(Qt.AlignLeft)
        self.val{i}.setText(val_text)
        self.val{i}.setTextInteractionFlags(Qt.TextSelectableByMouse)
        if lbl_text == "MIDI for Auralization: " or lbl_text == "Plugin: ":
            self.line{i} = QHLine()
            self.layout.addRow(self.line{i})
        self.layout.addRow(self.lbl{i}, self.val{i})
    else:
        self.genParamInfo(val_text)
else:
    self.lbl{i}.setText(lbl_text)
    if type(val_text) != dict:
        self.val{i}.setText(val_text)
    else:
        self.genParamInfo(val_text)
''')
            
            self.layout.addRow(self.buttonBox)
            self.loaded = True
            
        except KeyError:
            errorBox = QMessageBox()
            errorBox.setIcon(QMessageBox.Critical)
            errorBox.setText("Hashcode not found in the Database. Load another DB or try another file.")
            errorBox.exec_()
            
class About(QDialog): # window with information about the project
    def __init__(self):
        super().__init__()
        self.setWindowTitle("About")
        self.setWindowIcon(QIcon(ICON_PATH))
        buttons = QDialogButtonBox.Ok
        self.buttonBox = QDialogButtonBox(buttons)
        self.buttonBox.button(QDialogButtonBox.Ok).setText("Close")
        self.buttonBox.accepted.connect(self.accept)
        self.layout = QFormLayout()
        self.setLayout(self.layout)
        
        self.txt_about = QLabel(self)
        self.txt_links = QLabel(self)
        self.txt_licenses = QLabel(self)
        self.txt_about.setText("This Tool has been developed for the Projects DISKOS (BMBF) and MODAVIS (PhD) to execute quick auralizations \nwith traceable parameters and identifiers for virtual instruments and the corresponding MIDI- & Audio-Files.\n")
        self.txt_links.setText("More Information: <a href=\"https://github.com/modavis-project/\">https://github.com/modavis-project/</a>")
        self.txt_links.setOpenExternalLinks(True)
        self.txt_licenses.setText("License: <a href=\"https://www.gnu.org/licenses/gpl-3.0.en.html\">GPLv3</a>\nCopyright \u00a9 2022 by Dominik Ukolov")
        self.txt_licenses.setOpenExternalLinks(True)
        
        self.layout.addRow(self.txt_about)
        self.layout.addRow(self.txt_links)
        self.layout.addRow(self.txt_licenses)
        self.layout.addRow(self.buttonBox)

class QHLine(QFrame): # creates a horizontal line
    def __init__(self):
        super(QHLine, self).__init__()
        self.setFrameShape(QFrame.HLine)
        self.setFrameShadow(QFrame.Sunken)
        
class PathEdit(QLineEdit): # LineEdit which checks for double-click events
    doubleClicked = QtCore.pyqtSignal()
    def mouseDoubleClickEvent(self, event):
        self.doubleClicked.emit()
        super(PathEdit, self).mouseDoubleClickEvent(event)

# StyleSheets:
style_mainBt = """
QPushButton {
  background: #e7eaf0;
  border-style: outset;
  border-width: 2px;
  border-radius: 20px;
  border-color: black;
  color: #1a1e23;
  font: bold 16px;
  min-width: 10em;
  max-width: 250px;
  padding: 6px;
  }
QPushButton:hover {
    background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                  stop: 0 #edeef6, stop: 1 #d0d4ee);
    }
QPushButton:pressed {
    background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                  stop: 0 #dadbde, stop: 1 #f6f7fa);
    }
"""
style_mainCombo = """
QComboBox {
  background: #353d4a;
  border: 2px solid slategrey;
  border-radius: 3px;
  padding: 1px 18px 1px 210px;
  min-height: 2em;
  color: mintcream;
  font: 16px; 
  margin-left: 0px;
  }
QComboBox QAbstractItemView {
  border: 1px solid slategrey;
  background: #424c5c;
  selection-background-color: #353c49;
  color: gainsboro;
  }
"""

style_main = f"""
    Main {{    
        background-color: #424c5c;
        background-repeat: no-repeat;
        background-position: center;
    }}
    QComboBox {{
        background: white;
        border-style: outset;
        border: 1px solid grey;
        
    }}
    QComboBox::down-arrow {{
    image: url({cwd_css}/images/DropDownArrow.png);
    width: 14px;
    height: 14px;
    }}
    QStatusBar {{
        background: #e7eaf0;
        text-align: center;}}
"""
        
if __name__ == "__main__": # calls the start of the application
    app = QApplication(sys.argv)
    app.setStyleSheet(style_main)
    win = Start()
    sys.exit(app.exec_())