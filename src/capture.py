import sys
import threading
import NDIlib as ndi
from PIL import Image
from pystray import MenuItem as item
from pystray import Icon
import numpy as np
import dxcam
from os import path

import cv2 as cv
import socket


class NDISenderApp:
    def __init__(self):
        self.ndi_send = None
        self.sending = False
        self.capture_thread = None

    def start_sending(self):
        fps = 30
        camera = dxcam.create(output_color="BGRA")
        camera.start(target_fps=fps, video_mode=True)
        while self.sending:
            screenshot = camera.get_latest_frame()
            # ndi_image = Image.frombytes(
            #    "RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
            # low_res_image = ndi_image.resize((640, 360))
            image_data = np.array(screenshot)
            low_res_image = cv.resize(
                image_data, (640, 360), interpolation=cv.INTER_AREA)
            video_frame = ndi.VideoFrameV2()
            video_frame.data = low_res_image
            video_frame.FourCC = ndi.FOURCC_VIDEO_TYPE_BGRX
            video_frame.frame_rate_N = fps
            video_frame.frame_rate_D = 1
            video_frame.xres = 640
            video_frame.yres = 360
            ndi.send_send_video_v2(self.ndi_send, video_frame)
        camera.stop()

    def start_capture(self):
        self.ndi_send = ndi.send_create(self.send_settings)
        if (self.ndi_send is None):
            print("Error: Failed to create NDI sender")
            sys.exit(1)
        metadataFrame = ndi.MetadataFrame()
        metadataFrame.data = "<ndi_capabilities web_control=\"http://%IP%\" />"
        ndi.send_add_connection_metadata(self.ndi_send, metadataFrame)
        self.sending = True
        self.capture_thread = threading.Thread(target=self.start_sending)
        self.capture_thread.start()

    def stop_capture(self):
        self.sending = False
        if self.capture_thread:
            self.capture_thread.join()
            self.capture_thread = None

        if self.ndi_send:
            ndi.send_destroy(self.ndi_send)
            self.ndi_send = None

    def on_exit(self, icon, item):
        if self.sending:
            self.stop_capture()
        icon.stop()

    def toggle_capture(self):
        if self.sending:
            self.stop_capture()
        else:
            self.start_capture()
        self.icon.update_menu()

    def create_tray_app(self):
        menu = (
            item(socket.gethostname(), lambda item: None),
            item("Capturing Display", self.toggle_capture,
                 checked=lambda item: self.sending),
            item('Exit', self.on_exit))
        path_to_icon = path.abspath(path.join(path.dirname(__file__), 'ndi.ico'))
        ndi_icon = Image.open(path_to_icon)
        self.icon = Icon("NDI Low-Res Capture", ndi_icon,
                         "NDI Low-Res Capture", menu)
        self.icon.run()

    def main(self):
        if not ndi.initialize():
            return 0
        self.send_settings = ndi.SendCreate()
        self.send_settings.ndi_name = "Low-Res Capture"
        self.start_capture()
        self.create_tray_app()


if __name__ == "__main__":
    app = NDISenderApp()
    app.main()
