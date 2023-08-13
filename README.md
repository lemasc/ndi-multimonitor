# NDI Multi Monitor

## Motivation

NDI™ (Network Device Interface) is a technology designed to facilitate high-quality, low-latency video, audio, and data transmission over IP networks. By using NDI Tools bundle, you can share desktop screen (using NDI Screen Capture), transmit over the local network, and receive each sources using NDI Studio Monitor.

I'm at the environment that needs to monitor multiple computer screens simultaneously. However, the existing NDI Studio Monitor isn't designed to view multiple sources at the same time.

I find out that it can create a new window monitor for each source, but that's time consuming for multiple screens to create. I decided to write my own.

**Note: This project is made for internal use and for education It is not ready for production use.**

## Components

### NDI Multi-Monitor (`monitor.py`)

This Python script is a multi-source NDI™ receiver. You will be able to select sources to monitored, and then view all selected sources simultaneously on the grid layout.

### NDI Low-Res Screen Capture (`capture.py`)

To achieve more performance, you can use this script to capture the screen, and send the video using a lower resolution (640x360). This video stream is compatiable with all NDI™ receivers.

This script use a native screen capture library that is available on Windows only, but you can modify the code for your needs.

## Development

First, install Python and pip. Run the command to install all dependencies.

```
pip install -r requirements.txt
```

This project use `ndi-python`. However, you might need to build it manually. Follow the instructions [here](https://github.com/buresu/ndi-python#build) to build manually. 


For my current environment (Python 3.11 on Windows 64 bit), it should be able to install from the pre-built file located inside the `ndi` folder. But for me there's an edge case where it doesn't. So I rename the file and install it using this command.

```
pip install "ndi/ndi_python-5.1.1.5-cp311-none-any.whl"
```

You are now ready to code!

To build an executable for this project, install `pyinstaller`, and build according to each spec file. Run `pyinstaller capture.spec` and `pyinstaller monitor.spec` accordingly.

The output executable file is located at the `dist` folder.

## Running the build of this project

You must install the NDI™ 5 Runtime before running, which are available on each platform.

- Windows: http://ndi.link/NDIRedistV5
- MacOS: http://ndi.link/NDIRedistV5Apple
- Linux: https://downloads.ndi.tv/SDK/NDI_SDK_Linux/Install_NDI_SDK_v5_Linux.tar.gz

When you first launch the executable, the system may ask for adding an exception to Windows Firewall. You should allow it, and restart the program again.

# License

MIT