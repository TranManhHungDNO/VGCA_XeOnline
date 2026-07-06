import sys

from gui.sign_gui import SignGUI


def main(pdf_file=None):
    app = SignGUI(pdf_file=pdf_file)
    app.protocol("WM_DELETE_WINDOW", app._on_quit)
    app.mainloop()


if __name__ == "__main__":

    pdf = None

    if len(sys.argv) > 1:
        pdf = sys.argv[1]

    main(pdf)