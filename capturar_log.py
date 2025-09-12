# capturar_log.py
import time

class LogCapture:
    """
    Captura logs e mantém a última mensagem.
    Permite callback para atualizar UI automaticamente.
    """
    def __init__(self, ui_callback=None, delay: float = 1):
        self.last_message = None
        self.ui_callback = ui_callback  # função que será chamada quando o log mudar
        self.delay = delay              # atraso opcional em segundos

    def log(self, message: str):
        self.last_message = message
        print(message)  # opcional: mantém log no console
        if self.ui_callback:
            self.ui_callback(message)  # atualiza a interface
        if self.delay > 0:
            time.sleep(self.delay)     # aplica delay se configurado

    def get_last(self):
        return self.last_message


