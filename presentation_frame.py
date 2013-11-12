import Tkinter as tk
import PIL.ImageTk
import PIL.Image


class PresentationFrame(tk.Frame):

    def __init__(self, parent, screen_position):
        tk.Frame.__init__(self, parent)

        self.parent = parent
        self.screen_position = screen_position

        self.can = None
        self.can_img = None
        self.image = None
        self.resized_photo = None

        self.init_ui()

    def change_image(self, image):
        self.image = image
        self.event_generate("<<paint_canvas>>")

    def fade_out(self):
        self.image = None
        self.resized_photo = None
        self.event_generate("<<paint_canvas>>")

    def _paint_canvas(self, event=None):
        if not self.image is None:
            self.resized_photo = self.image.resize(self.screen_position[0:2], PIL.Image.ANTIALIAS)
            self.resized_photo = PIL.ImageTk.PhotoImage(self.resized_photo)
            self.can.delete(tk.ALL)
            self.can_img = self.can.create_image(0, 0, image=self.resized_photo, anchor=tk.NW)
        else:
            self.can.delete(tk.ALL)

    def init_ui(self):
        self.bind("<<quit>>", self.quit_handler)
        self.parent.title("Presentation window")

        #self.image = PIL.Image.open("img1.jpg")

        self.parent.overrideredirect(1)
        self.parent.geometry("%dx%d+%d+%d" % self.screen_position)
        self.parent.configure(background='black')

        self.can = tk.Canvas(self, bd=0, highlightthickness=0, bg="black")
        self.can.place(relwidth=1, relheight=1)

        #self.fade_label = tk.Label(self, bg='black')
        #self.fade_label.place(relwidth=1, relheight=1)

        self.pack(fill=tk.BOTH, expand=1)

        self.bind("<<paint_canvas>>", self._paint_canvas)
        self.event_generate("<<paint_canvas>>")

    def quit_handler(self, event):
        self.parent.destroy()


def main():

    root = tk.Tk()
    root.geometry("300x200+300+300")
    app = PresentationFrame(root, (1440, 900, 0, 300))
    app.change_image(PIL.Image.open("example/img1.jpg"))
    root.mainloop()


if __name__ == '__main__':
    main()
