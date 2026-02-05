See https://github.com/stevenryoung/audio_delay_wasm for a browser based version of this that will capture a radio stream in the browser.


Sports Radio Delay
==============================

Python tool to delay radio (or any generic audio input)

## Use

RADIO >> AUDIO CABLE >> PC >> (OPTIONAL) AUDIO CABLE >> (OPTIONAL) SPEAKERS

Run `radiodelay/__main__.py` and adjust delay as appropriate.

## Why?

National broadcast announcers are not as interesting to listen to as local broadcasters when you are watching your team play. Thus, it is nice to listen to your local radio broadcast when you are watching the TV broadcast. However, radio broadcasts are often 10-30 seconds ahead of the TV broadcast and ruin the experience of watching the game. You cannot make your TV play the game sooner with your DVR, so you must make the radio play later. This tool allows you to do that.

## Why not just get the radio broadcast online?

Online radio often does not allow you to pause in order to delay the radio. Tools could be written to capture these streams, but this would rely on the radio stations not changing their online player. There are probably some things that could be done to capture the audio from the online player, however, I just found this to be the simplest way to tackle the problem. It is simple enough, and reliable enough, for my purposes and is straight forward enough for both me to use and people I know who are only mildly tech literate.

## Requirements

[Python 3.10+](https://www.python.org/downloads/)

[PyAudio](http://people.csail.mit.edu/hubert/pyaudio/)

Tested on Ubuntu, Raspberry Pi OS and Windows 11.

## Pip Install
- Windows
  - To avoid fussing with compilation tools and dev libraries, install a version of Python that has a PyAudio "wheel" package available (e.g., CPython 3.13). [Consult this PyAudio release list to find supported versions](https://pypi.org/project/PyAudio/#files), then [get the corresponding Python installer](https://www.python.org/downloads/).
  - `python -m pip install radiodelay`
    - Note the script path described in the warning
  - `C:\Users\MyUserName\AppData\Local\Programs\Python\Python313\Scripts\radiodelay.exe`
    - Adjust path as appropriate based on the message during "pip install"

- Ubuntu, Mac OSX
  - Make sure to install portaudio first (sudo apt install portaudio19-dev or brew install portaudio)
  - `python -m pip install radiodelay`
  - `radiodelay`
