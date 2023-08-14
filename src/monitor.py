from fractions import Fraction
import sys
import PySimpleGUI as sg
import NDIlib as ndi
import pygame

# Python function that recieve a dimension and return the closest 16:9 dimension
# This is used to set the window size to the closest 16:9 dimension
# Dimension is a tuple (width, height)


def getClosest16_9Dimension(dimension):
    width = dimension[0]
    height = dimension[1]
    ratio = Fraction(width, height)
    if ratio == Fraction(16, 9):
        return dimension
    elif ratio > Fraction(16, 9):
        return (int(16 * height / 9), height)
    else:
        return (width, int(9 * width / 16))


def source_names(sourceArray):
    return [source.ndi_name for source in sourceArray]


def get_source(sourceArray, sourceName):
    return [source for source in sourceArray if source.ndi_name == sourceName][0]


class NDIConsoleApp:
    def __init__(self):
        self.sources = []
        self.selectedSources = []
        self.sourceRecievers = []
        self.ndi_find = None
        self.showMonitor = False

    def setInitialSources(self):
        # Initialize the list of sources
        while True:
            if not ndi.find_wait_for_sources(self.ndi_find, 500):
                print('No change to the sources found.')
                break
            self.sources = ndi.find_get_current_sources(self.ndi_find)

        # Initialize the list of selected sources with all the sources found
        self.selectedSources = [
            source for source in self.sources if "Remote Connection" not in source.ndi_name]

    def create_console_window(self):
        sg.theme('dark grey 9')   # Add a touch of color
        self.setInitialSources()
        sources_selector_layout = [[
            sg.Listbox(values=source_names(self.sources), size=(30, 6),
                       key='-SOURCES-',  expand_x=True, expand_y=True, enable_events=True),
            sg.Column([
                [sg.Button("Refresh")],
                [sg.Button("Add")],
                [sg.Button("Remove")]
            ]),
            sg.Listbox(values=source_names(self.selectedSources), size=(30, 6),
                       key='-SHOWNSOURCES-',  expand_x=True, expand_y=True, enable_events=True)
        ]]

        # All the stuff inside your window.
        layout = [[sg.Text('Select sources to be monitored.')],
                  [sg.Column(sources_selector_layout,
                             expand_x=True, expand_y=True)],
                  [
            sg.OK("Start"), sg.Cancel("Stop")]]

        # Create the Window
        self.window = sg.Window('NDI Multi Monitor', layout, size=(900, 300))

        # Event Loop to process "events" and get the "values" of the inputs
        while True:
            event, values = self.window.read()
            if event == sg.WIN_CLOSED or event == 'Cancel':  # if user closes window or clicks cancel
                break
            if event == "Refresh":
                newSources = ndi.find_get_current_sources(self.ndi_find)
                # Sources that are removed should also be removed from the selected sources, if included.
                for source in self.sources:
                    if source not in newSources:
                        if source in self.selectedSources:
                            self.selectedSources.remove(source)

                self.window['-SOURCES-'].update(source_names(self.sources))
            elif event == "Add" and values['-SOURCES-'] != []:
                # Add the currently focused source on the listbox to the list of selected sources
                source = get_source(self.sources, values['-SOURCES-'][0])
                if source not in self.selectedSources:
                    self.selectedSources.append(source)
                    self.window['-SHOWNSOURCES-'].update(
                        source_names(self.selectedSources))
            elif event == "Remove" and values['-SHOWNSOURCES-'] != []:
                # Remove the currently focused source on the listbox to the list of selected sources
                source = get_source(self.sources, values['-SHOWNSOURCES-'][0])
                if source in self.selectedSources:
                    self.selectedSources.remove(source)
                self.window['-SHOWNSOURCES-'].update(
                    source_names(self.selectedSources))
            elif event == "Start":
                if (len(self.selectedSources) > 0 and self.showMonitor == False):
                    self.showMonitor = True
                    self.window.hide()
                    self.create_monitor_window()
                    self.destroy_receive_sources()

        self.window.close()

    def create_monitor_window(self):
        self.destroy_receive_sources()
        self.init_receive_sources()
        pygame.init()
        pygame.display.set_caption('NDI Multi Monitor')
        self.monitor = pygame.display.set_mode((1366, 768), pygame.RESIZABLE)

        targetSize = (1366/3, 768/3)

        secondary_surface = pygame.Surface(
            (1366, 768))  # Create secondary surface

        while self.showMonitor:
            for event in pygame.event.get():
                if event.type == pygame.QUIT or event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    self.showMonitor = False
                elif event.type == pygame.VIDEORESIZE:
                    dimension = getClosest16_9Dimension(event.dict['size'])
                    self.monitor = pygame.display.set_mode(
                        dimension, pygame.RESIZABLE)
                    targetSize = (dimension[0]/3, dimension[1]/3)
                    secondary_surface = pygame.Surface(
                        dimension)
                    # Reset the position of the images
                    for i in range(len(self.sourceRecievers)):
                        self.sourceRecievers[i]["pos"] = None

            # secondary_surface.fill((0, 0, 0))

            for i in range(len(self.sourceRecievers)):
                t, v, _, _ = ndi.recv_capture_v2(
                    self.sourceRecievers[i]["source"], 1500)
                if t != ndi.FRAME_TYPE_VIDEO:
                    continue
                # Calculate the position of the image on the monitor if it is not set
                # We want to display the images in a grid 3x3
                if self.sourceRecievers[i]["pos"] is None:
                    previousPos = self.sourceRecievers[i - 1]["pos"]
                    if previousPos is None:
                        previousPos = (-targetSize[0], 0)

                    self.sourceRecievers[i]["pos"] = (
                        previousPos[0] + targetSize[0], previousPos[1])
                    if self.sourceRecievers[i]["pos"][0] >= self.monitor.get_width():
                        self.sourceRecievers[i]["pos"] = (
                            0, previousPos[1] + targetSize[1])

                image = pygame.image.frombuffer(
                    v.data, (v.xres, v.yres), 'BGRA')
                secondary_surface.blit(pygame.transform.scale(
                    image, targetSize), self.sourceRecievers[i]["pos"])
                ndi.recv_free_video_v2(self.sourceRecievers[i]["source"], v)

            # Blit the entire secondary surface onto the screen
            self.monitor.blit(secondary_surface, (0, 0))
            pygame.display.update()

        self.destroy_receive_sources()
        pygame.quit()
        self.window.un_hide()

    def init_receive_sources(self):
        for source in self.selectedSources:
            recv_create_desc = ndi.RecvCreateV3()
            recv_create_desc.color_format = ndi.RECV_COLOR_FORMAT_BGRX_BGRA
            recv_create_desc.bandwidth = ndi.RECV_BANDWIDTH_LOWEST
            receiver = {
                "name": source.ndi_name,
                "source": ndi.recv_create_v3(recv_create_desc),
                "pos": None,
            }
            if (receiver["source"] is None):
                ndi.recv_destroy(receiver["source"])
                continue
            ndi.recv_connect(receiver["source"], source)

            self.sourceRecievers.append(receiver)

    def destroy_receive_sources(self):
        for receiver in self.sourceRecievers:
            ndi.recv_destroy(receiver["source"])
        self.sourceRecievers = []

    def main(self):
        if not ndi.initialize():
            return 0

        self.ndi_find = ndi.find_create_v2()

        if self.ndi_find is None:
            return 0

        self.create_console_window()

        if self.ndi_find is not None:
            ndi.find_destroy(self.ndi_find)
            ndi.destroy()


if __name__ == "__main__":
    app = NDIConsoleApp()
    sys.exit(app.main())
