import sys

from gui.sign_gui import SignGUI


def main():
    app = SignGUI()
    app.protocol("WM_DELETE_WINDOW", app._on_quit)
    app.mainloop()


if __name__ == "__main__":
    main()
