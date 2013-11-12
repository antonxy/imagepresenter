import PIL.Image
import Tkinter as tk
import tkFont
import tkFileDialog
import tkMessageBox
import csv
import Queue
import tkSimpleDialog
import ConfigParser
import os
from presentation_frame import PresentationFrame
from network_listener import NetworkListener
import monitor


class MainFrame(tk.Frame):
    def __init__(self, parent):
        tk.Frame.__init__(self, parent)

        self.parent = parent

        self.presentation_window = None
        self.presentation_frame = None
        self.presentation_window_position = (1440, 900, 0, 0)

        self.slides_listbox = None
        self.slides_list = None

        self.edit_id = tk.StringVar()
        self.edit_desc = tk.StringVar()
        self.edit_image = tk.StringVar()

        self.network_listener = NetworkListener(self.schedule_action)

        self.actions_queue = Queue.Queue(1)

        self.read_config()

        self.init_ui()

    def init_ui(self):

        self.parent.title("ImagePresenter")

        self.parent.protocol("WM_DELETE_WINDOW", self.exit_handler)

        # ------
        # LAYOUT
        # ------

        top_frame = tk.Frame(self)
        top_frame.pack(fill=tk.X)

        vertical_center_frame = tk.Frame(self)
        vertical_center_frame.pack(fill=tk.BOTH, expand=1)

        left_frame = tk.Frame(vertical_center_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.Y)

        right_frame = tk.Frame(vertical_center_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.Y)

        main_frame = tk.Frame(vertical_center_frame, relief=tk.RAISED, borderwidth=1)
        main_frame.pack(fill=tk.BOTH, expand=1)

        bottom_frame = tk.Frame(self)
        bottom_frame.pack(fill=tk.X)

        # -------
        # WIDGETS
        # -------

        # Menu buttons
        tk.Button(top_frame, text="Load", command=self.load_slides_file).pack(side=tk.LEFT)

        tk.Button(top_frame, text="Save", command=self.save_slides_file).pack(side=tk.LEFT)

        tk.Button(top_frame, text="Save As", command=self.save_slides_file_as).pack(side=tk.LEFT)

        tk.Button(top_frame, text="Screen setup", command=self.screen_setup).pack(side=tk.LEFT)

        tk.Button(top_frame, text="Show", command=self.show_screen).pack(side=tk.LEFT)

        tk.Button(top_frame, text="Hide", command=self.hide_screen).pack(side=tk.LEFT)


        # Left buttons
        tk.Button(left_frame, text="Fade In", command=self.fade_in_btn).pack()

        tk.Button(left_frame, text="Fade Out", command=self.fade_out_btn).pack()

        # Right buttons
        tk.Button(right_frame, text="Move up", command=lambda: self.slides_list.move_selected(-1)).pack()

        tk.Button(right_frame, text="Move down", command=lambda: self.slides_list.move_selected(1)).pack()

        tk.Button(right_frame, text="Delete", command=self.edit_slide_delete).pack()

        slide_info_frame = tk.Frame(right_frame)
        slide_info_frame.pack()

        #Edit Slides
        tk.Label(slide_info_frame, text='ID:').grid(row=0, sticky=tk.W)
        tk.Label(slide_info_frame, text='Descr:').grid(row=1, sticky=tk.W)
        tk.Label(slide_info_frame, text='Image:').grid(row=2, sticky=tk.W)

        id_entry = tk.Entry(slide_info_frame, textvariable=self.edit_id)
        desc_entry = tk.Entry(slide_info_frame, textvariable=self.edit_desc)
        image_label = tk.Label(slide_info_frame, textvariable=self.edit_image, wraplength=170)

        id_entry.grid(row=0, column=1)
        desc_entry.grid(row=1, column=1)
        image_label.grid(row=2, column=1)

        edit_slide_buttons_frame = tk.Frame(slide_info_frame)
        edit_slide_buttons_frame.grid(row=3, columnspan=2)

        tk.Button(edit_slide_buttons_frame, text='Add', command=self.edit_slide_add).pack(side=tk.RIGHT)
        tk.Button(edit_slide_buttons_frame, text='Update', command=self.edit_slide_update).pack(side=tk.RIGHT)
        tk.Button(edit_slide_buttons_frame, text='Clear', command=self.edit_slide_clear).pack(side=tk.RIGHT)
        tk.Button(edit_slide_buttons_frame, text='Load', command=self.edit_slide_load_image).pack(side=tk.RIGHT)

        # Network info
        ip_label = tk.Label(bottom_frame, text="IP: 0.0.0.0")
        ip_label.pack(side=tk.LEFT)

        port_label = tk.Label(bottom_frame, text="Port: 20098")
        port_label.pack(side=tk.LEFT)

        status_label = tk.Label(bottom_frame, text="Status: listening")
        status_label.pack(side=tk.LEFT)

        #tk.Button(bottom_frame, text="Configure").pack(side=tk.LEFT)

        #Main list
        list_font = tkFont.Font(family="Courier")
        self.slides_listbox = tk.Listbox(main_frame, font=list_font)
        self.slides_listbox.pack(fill=tk.BOTH, expand=tk.YES)
        self.slides_listbox.bind('<Double-Button-1>', self.edit_slide_prefill)

        self.slides_list = SlideList()
        self.slides_list.connect_listbox(self.slides_listbox)

        self.bind('<<exec_action>>', self.execute_action)
        self.network_listener.start()

        self.pack(fill=tk.BOTH, expand=1)

    def read_config(self):
        try:
            config = ConfigParser.ConfigParser()
            config.read('config.ini')
            self.presentation_window_position = tuple([int(config.get('Presentation', o)) for o in ['sx', 'sy', 'ox', 'oy']])
        except:
            print 'Could not read config'

    def write_config(self):
        config = ConfigParser.ConfigParser()
        config.add_section('Presentation')
        config.set('Presentation', 'sx', self.presentation_window_position[0])
        config.set('Presentation', 'sy', self.presentation_window_position[1])
        config.set('Presentation', 'ox', self.presentation_window_position[2])
        config.set('Presentation', 'oy', self.presentation_window_position[3])
        with open('config.ini', 'wb') as cfg_file:
            config.write(cfg_file)

    def schedule_action(self, action):
        self.actions_queue.put(action)
        self.event_generate('<<exec_action>>')

    def execute_action(self, event):
        try:
            action = self.actions_queue.get_nowait()
        except Queue.Empty:
            return
        try:
            l = action.strip().split(':', 1)
            if len(l) < 0:
                return

            print 'Received action: ', l

            if l[0] == 'FADEIN':
                if not self.presentation_frame is None:
                    self.presentation_frame.change_image(self.slides_list.get_by_id(l[1]).image)
            elif l[0] == 'FADEOUT':
                if not self.presentation_frame is None:
                    self.presentation_frame.fade_out()
        except StandardError as e:
            print "Error executing action %s:%s" % (action, e.message)

    def exit_handler(self):
        self.network_listener.join()
        self.write_config()
        self.quit()

    def show_screen(self):
        if self.presentation_frame is None:
            self.presentation_window = tk.Toplevel(self.parent)
            self.presentation_frame = PresentationFrame(self.presentation_window, self.presentation_window_position)

    def hide_screen(self):
        if not self.presentation_frame is None:
            self.presentation_frame.event_generate('<<quit>>')
            self.presentation_frame = None
            self.presentation_window = None

    def load_slides_file(self):
        path = tkFileDialog.askopenfilename()
        if path != "":
            try:
                self.slides_list.load_from_file(path)
            except csv.Error:
                tkMessageBox.showerror('Load slide list', 'Error parsing file')
            except IOError:
                tkMessageBox.showerror('Load slide list', 'Could not open file')
            except StandardError as e:
                tkMessageBox.showerror('Load slide list', 'Unknown Error opening file:\n%s' % e.message)

    def save_slides_file(self):
        path = self.slides_list.filepath
        if path != "":
            try:
                self.slides_list.save_to_file(path)
            except csv.Error:
                tkMessageBox.showerror('Save slide list', 'Error with csv writer')
            except IOError:
                tkMessageBox.showerror('Save slide list', 'Could not write file')
            except StandardError as e:
                tkMessageBox.showerror('Save slide list', 'Unknown Error saving file:\n%s' % e.message)
        else:
            self.save_slides_file_as()

    def save_slides_file_as(self):
        path = tkFileDialog.asksaveasfilename()
        if path != "":
            try:
                self.slides_list.save_to_file(path)
            except csv.Error:
                tkMessageBox.showerror('Save slide list', 'Error with csv writer')
            except IOError:
                tkMessageBox.showerror('Save slide list', 'Could not write file')
            except StandardError as e:
                tkMessageBox.showerror('Save slide list', 'Unknown Error saving file:\n%s' % e.message)

    def fade_in_btn(self):
        if not self.presentation_frame is None:
            item = self.slides_list.get_selected()
            if not item is None:
                self.presentation_frame.change_image(item.image)

    def fade_out_btn(self):
        if not self.presentation_frame is None:
            self.presentation_frame.fade_out()

    def edit_slide_clear(self):
        self.edit_id.set('')
        self.edit_desc.set('')
        self.edit_image.set('')

    def edit_slide_add(self):
        self.slides_list.append(SlideListItem(self.edit_id.get(), self.edit_desc.get(), self.edit_image.get()))
        self.edit_slide_clear()

    def edit_slide_update(self):
        self.slides_list.update_selected(self.edit_id.get(), self.edit_desc.get(), self.edit_image.get())
        self.edit_slide_clear()

    def edit_slide_load_image(self):
        path = tkFileDialog.askopenfilename()
        if path != '':
            self.edit_image.set(path)

    def edit_slide_prefill(self, event=None):
        s = self.slides_list.get_selected()
        if not s is None:
            self.edit_id.set(s.id)
            self.edit_desc.set(s.desc)
            self.edit_image.set(s.path)

    def edit_slide_delete(self):
        s = self.slides_list.get_selected()
        if not s is None:
            self.slides_list.remove(s)

    def screen_setup(self):
        d = ScreenSetupDialog(self, self.presentation_window_position)
        if not d.result is None:
            self.presentation_window_position = d.result


class SlideList(object):
    def __init__(self):
        self._list = []
        self.listbox = None
        self.filepath = ""

    def append(self, items):
        if type(items) is list:
            for e in items:
                e.load_image_if_necessary()
                self._list.append(e)
        else:
            items.load_image_if_necessary()
            self._list.append(items)
        self.refresh_list()

    def clear(self):
        self._list = []
        self.refresh_list()

    def remove(self, items):
        if type(items) is list:
            for e in items:
                self._list.remove(e)
        else:
            self._list.remove(items)
        self.refresh_list()

    def update_selected(self, idf, desc, path):
        i = self.get_selected()
        if not i is None:
            i.id = idf
            i.desc = desc
            i.path = path
            i.load_image()
            self.refresh_list()

    def connect_listbox(self, listbox):
        self.listbox = listbox
        self.refresh_list()

    def disconnect_listbox(self):
        self.listbox = None

    def get_selected(self):
        items = map(int, self.listbox.curselection())
        if len(items) > 0:
            return self._list[items[0]]
        else:
            return None

    def move_selected(self, offset):
        items = map(int, self.listbox.curselection())
        if len(items) > 0:
            i = items[0]
            self._list.insert(i + offset, self._list.pop(i))
            self.refresh_list()
            self.listbox.selection_set(i + offset)

    def get_by_id(self, idf):
        for e in self._list:
            if e.id == idf:
                return e
        return None

    def refresh_list(self):
        if not self.listbox is None:
            self.listbox.delete(0, tk.END)
            for e in self._list:
                self.listbox.insert(tk.END, e)

    def load_from_file(self, path):
        self.clear()
        self.filepath = path
        with open(path, 'rb') as csvfile:
            reader = csv.reader(csvfile)
            items = [SlideListItem(r[0], r[1], self.make_path_absolute(r[2])) for r in reader]
            self.append(items)

    def save_to_file(self, path):
        self.filepath = path
        with open(path, 'wb') as csvfile:
            writer = csv.writer(csvfile)
            for e in self._list:
                writer.writerow([e.id, e.desc, self.make_path_relative(e.path)])

    def make_path_relative(self, path):
        return os.path.relpath(path, os.path.dirname(self.filepath))

    def make_path_absolute(self, path):
        return os.path.normpath(os.path.join(os.path.dirname(self.filepath), path))


class SlideListItem(object):
    def __init__(self, idf=None, desc=None, path=None, image=None):
        self.id = idf
        self.desc = desc
        self.path = path
        self.image = image

    def load_image(self):
        self.image = PIL.Image.open(self.path)

    def load_image_if_necessary(self):
        if self.image is None:
            self.load_image()

    def __str__(self):
        return "%10s | %s" % (self.id, self.desc)


class ScreenSetupDialog(tkSimpleDialog.Dialog):
    def __init__(self, parent, init_value):
        self.s_sx = tk.IntVar(value=init_value[0])
        self.s_sy = tk.IntVar(value=init_value[1])
        self.s_ox = tk.IntVar(value=init_value[2])
        self.s_oy = tk.IntVar(value=init_value[3])
        self.screen_sizes = monitor.monitor_areas()
        self.list = None
        tkSimpleDialog.Dialog.__init__(self, parent)

    def body(self, master):
        tk.Label(master, text='x').grid(row=0, column=1)
        tk.Label(master, text='y').grid(row=0, column=2)
        tk.Label(master, text='size').grid(row=1, column=0)
        tk.Label(master, text='offset').grid(row=2, column=0)

        e1 = tk.Entry(master, textvariable=self.s_sx).grid(row=1, column=1) #Initial focus
        tk.Entry(master, textvariable=self.s_sy).grid(row=1, column=2)
        tk.Entry(master, textvariable=self.s_ox).grid(row=2, column=1)
        tk.Entry(master, textvariable=self.s_oy).grid(row=2, column=2)

        self.list = tk.Listbox(master)
        self.list.grid(row=3, column=1, columnspan=3)
        [self.list.insert(tk.END, e) for e in self.screen_sizes]
        self.list.bind('<Double-Button-1>', self.select_screensize)

        return e1

    def select_screensize(self, event=None):
        items = map(int, self.list.curselection())
        if len(items) > 0:
            item = self.screen_sizes[items[0]]
            self.s_sx.set(item[0])
            self.s_sy.set(item[1])
            self.s_ox.set(item[2])
            self.s_oy.set(item[3])
            print(self.screen_sizes[items[0]])

    def validate(self):
        try:
            self.result = (int(self.s_sx.get()), int(self.s_sy.get()), int(self.s_ox.get()), int(self.s_oy.get()))
            return 1
        except ValueError:
            tkMessageBox.showwarning("Bad Input", "Only Integers allowed")
            return 0


def main():
    root = tk.Tk()
    root.geometry("700x400+300+300")
    app = MainFrame(root)
    root.mainloop()
    app.network_listener.join()


if __name__ == '__main__':
    main()
