import threading
import cursor
from halo import Halo
from halo._utils import decode_utf_8_text
from ipywidgets.widgets import Output
from IPython.display import display


def download_file_from_google_drive(gid, destination):
    import requests
    GGL_URL = "https://docs.google.com/uc?export=download"
    CHUNK_SIZE = 32768

    def get_confirm_token(response):
        for key, value in response.cookies.items():
            if key.startswith('download_warning'):
                return value
        return None

    print('asasas')
    session = requests.Session()
    response = session.get(GGL_URL, params = { 'id': gid }, stream = True)

    if not response.status_code == requests.codes.ok:
        raise requests.ConnectionError('Invalid request')

    token = get_confirm_token(response)

    if token:
        response = session.get(GGL_URL, params = { 'id': gid, 'confirm': token }, stream = True)

    with open(destination, "wb") as f:
        for chunk in response.iter_content(CHUNK_SIZE):
            if chunk: # filter out keep-alive new chunks
                f.write(chunk)

class HaloNotebook(Halo):
    CLEAR_LINE = '\033[K'

    def __init__(self, text='', color='cyan', spinner=None, animation=None, interval=-1, enabled=True, stream=None):

        super(HaloNotebook, self).__init__(text, color, spinner, animation, interval, enabled, stream)
        self.output = self._make_output_widget()

    def _make_output_widget(self):
        return Output()

    # TODO: using property and setter
    def _output(self, text=''):
        return ({'name': 'stdout', 'output_type': 'stream', 'text': text},)

    def clear(self):
        if not self._enabled:
            return self

        with self.output:
            self.output.outputs += self._output('\r')
            self.output.outputs += self._output(self.CLEAR_LINE)

        self.output.outputs = self._output()
        return self

    def _render_frame(self):
        frame = self.frame()
        output = '\r{0}'.format(frame)
        with self.output:
            self.output.outputs += self._output(output)

    def start(self, text=None):
        if text is not None:
            self._text = self._get_text(text, animation=None)

        if not self._enabled or self._spinner_id is not None:
            return self

        if self._stream.isatty():
            cursor.hide()

        self.output = self._make_output_widget()
        display(self.output)
        self._stop_spinner = threading.Event()
        self._spinner_thread = threading.Thread(target=self.render)
        self._spinner_thread.setDaemon(True)
        self._render_frame()
        self._spinner_id = self._spinner_thread.name
        self._spinner_thread.start()

        return self

    def stop_and_persist(self, options={}):
        if type(options) is not dict:
            raise TypeError('Options passed must be a dictionary')

        if 'symbol' in options and options['symbol'] is not None:
            symbol = decode_utf_8_text(options['symbol'])
        else:
            symbol = ' '

        if 'text' in options and options['text'] is not None:
            text = decode_utf_8_text(options['text'])
        else:
            text = self._text['original']

        text = text.strip()

        self.stop()

        output = '\r{0} {1}\n'.format(symbol, text)

        with self.output:
            self.output.outputs = self._output(output)
