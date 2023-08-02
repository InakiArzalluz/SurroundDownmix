import tkinter as tk
from tkinter import ttk
import threading
import logic

if __name__ == '__main__':
    # initialize app
    bg_colour = '#3d6466'
    root = tk.Tk()
    root.title('SurroundDownmix')
    root.eval('tk::PlaceWindow . center')

    def load_frame2(option: int):
        threading.Thread(target=logic.processFile, args=(option,)).start() 

    def load_frame1():

        style = ttk.Style()
        style.configure("BW.TLabel", foreground="white", background=bg_colour, font=('TkMenuFont', 13))
        style.configure("BW.TFrame", background=bg_colour)
        style.configure("BW.TButton", font=('TkHeadingFont', 13), bg='#28393a', fg='white', activebackground='#badee2', activeforeground='black')

        frame1 = ttk.Frame(root, width=500, height=500, style="BW.TFrame")
        frame1.grid(row=0,column=0)
        frame1.pack_propagate(False)

        # frame1 widgets
        # logo_img = ImageTk.PhotoImage(file=assets/logo.png)
        # logo_widget = tk.Label(frame1, image=logo_img, bg=bg_colour)
        # logo_widget.image = logo_img
        # logo_widget.pack()

        # Create the text
        pick_widget = ttk.Label(
            frame1,
            text='Select an algorithm',
            style="BW.TLabel"
            ).pack(pady=10)
        

        # Create the options
        options_list = [ "1.  FFmpeg's default", "2.  With vol. boost", "3.  Don't discard LFE channel", "4.  Nightmode"]
        value_inside = tk.StringVar(frame1)
        
        # Create the Optionmenu
        question_menu = ttk.OptionMenu(
            frame1,
            value_inside,
            options_list[1],  # Modify it, such that it remembers the previous selection
            *options_list
            ).pack()

        # Create the accept Button
        button_widget = ttk.Button(
            frame1,
            text='Accept',
            style='BW.TButton',
            cursor='hand2',
            command=lambda:load_frame2( int(value_inside.get()[0])-1 ) # option number in tuple 
            ).pack(pady=10)


    # run app
    load_frame1()
    root.mainloop()
