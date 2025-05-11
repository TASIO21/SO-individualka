import sys
import os
import winreg
import subprocess
import requests
import re
import logging
import webbrowser
import platform
from datetime import datetime
from bs4 import BeautifulSoup
from PyQt5.QtWidgets import (QApplication, QMainWindow, QTabWidget, QVBoxLayout, QPushButton,
                             QWidget, QTextEdit, QLabel, QLineEdit, QMessageBox, QGridLayout,
                             QProgressBar)
from PyQt5.QtCore import Qt, QThread, pyqtSignal

# Настройка логирования
logging.basicConfig(
    filename='browser_checker.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


class SystemScanThread(QThread):
    progress_update = pyqtSignal(int)
    scan_complete = pyqtSignal(str)

    def __init__(self):
        super().__init__()

    def run(self):
        try:
            result = "==== Сканирование системы ====\n"

            # Информация о системе
            self.progress_update.emit(10)
            result += f"Операционная система: {platform.system()} {platform.release()}\n"
            result += f"Версия: {platform.version()}\n"
            result += f"Архитектура: {platform.machine()}\n\n"

            # Информация о процессоре
            self.progress_update.emit(30)
            result += f"Процессор: {platform.processor()}\n"

            # Информация о памяти (только для Windows)
            if platform.system() == 'Windows':
                self.progress_update.emit(50)
                mem_info = subprocess.check_output(['systeminfo'], text=True)
                physical_memory = re.search(r'Total Physical Memory:\s*([\d,]+)', mem_info)
                if physical_memory:
                    result += f"Оперативная память: {physical_memory.group(1)}\n\n"

            # Список запущенных процессов
            self.progress_update.emit(70)
            result += "Запущенные процессы:\n"

            if platform.system() == 'Windows':
                processes = subprocess.check_output(['tasklist'], text=True)
                top_processes = processes.split('\n')[:20]
                result += '\n'.join(top_processes) + "\n...\n"

            # Информация о дисках
            self.progress_update.emit(90)
            result += "\nИнформация о дисках:\n"

            if platform.system() == 'Windows':
                drives = subprocess.check_output(['wmic', 'logicaldisk', 'get', 'caption,freespace,size,volumename'],
                                                 text=True)
                result += drives + "\n"

            self.progress_update.emit(100)
            self.scan_complete.emit(result)

            logging.info("Сканирование системы выполнено успешно")
        except Exception as e:
            logging.error(f"Ошибка при сканировании системы: {str(e)}")
            self.scan_complete.emit(f"Ошибка при сканировании: {str(e)}")


class BrowserCheckerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.scan_thread = None
        logging.info("Приложение запущено")

    def initUI(self):
        self.setWindowTitle('Проверка браузеров')
        self.setGeometry(100, 100, 800, 600)

        # Создаем вкладки
        self.tabs = QTabWidget()
        self.browser_tab = QWidget()
        self.system_tab = QWidget()
        self.url_tab = QWidget()

        self.tabs.addTab(self.browser_tab, "Браузеры")
        self.tabs.addTab(self.system_tab, "Сканирование системы")
        self.tabs.addTab(self.url_tab, "Открытие URL")

        # Настройка вкладки браузеров
        self.setup_browser_tab()

        # Настройка вкладки сканирования системы
        self.setup_system_tab()

        # Настройка вкладки открытия URL
        self.setup_url_tab()

        self.setCentralWidget(self.tabs)

        # Проверяем автозапуск
        self.check_autostart()

    def setup_browser_tab(self):
        layout = QVBoxLayout()

        # Кнопка проверки браузеров
        check_btn = QPushButton('Проверить версии браузеров')
        check_btn.clicked.connect(self.check_browsers)
        layout.addWidget(check_btn)

        # Кнопка настройки автозапуска
        autostart_btn = QPushButton('Включить/Выключить автозапуск')
        autostart_btn.clicked.connect(self.toggle_autostart)
        layout.addWidget(autostart_btn)

        # Текстовое поле для вывода результатов
        self.browser_output = QTextEdit()
        self.browser_output.setReadOnly(True)
        layout.addWidget(self.browser_output)

        self.browser_tab.setLayout(layout)

    def setup_system_tab(self):
        layout = QVBoxLayout()

        # Кнопка сканирования системы
        scan_btn = QPushButton('Сканировать систему')
        scan_btn.clicked.connect(self.scan_system)
        layout.addWidget(scan_btn)

        # Прогресс бар
        self.progress_bar = QProgressBar()
        layout.addWidget(self.progress_bar)

        # Текстовое поле для вывода результатов
        self.system_output = QTextEdit()
        self.system_output.setReadOnly(True)
        layout.addWidget(self.system_output)

        self.system_tab.setLayout(layout)

    def setup_url_tab(self):
        layout = QGridLayout()

        # Поле ввода URL
        url_label = QLabel('Введите URL:')
        layout.addWidget(url_label, 0, 0)

        self.url_input = QLineEdit()
        self.url_input.setText('https://')
        layout.addWidget(self.url_input, 0, 1)

        # Кнопка открытия URL
        open_url_btn = QPushButton('Открыть URL')
        open_url_btn.clicked.connect(self.open_url)
        layout.addWidget(open_url_btn, 1, 0, 1, 2)

        # История открытых URL
        history_label = QLabel('История:')
        layout.addWidget(history_label, 2, 0, 1, 2)

        self.url_history = QTextEdit()
        self.url_history.setReadOnly(True)
        layout.addWidget(self.url_history, 3, 0, 1, 2)

        self.url_tab.setLayout(layout)

    def check_browsers(self):
        self.browser_output.clear()
        self.browser_output.append("Проверка версий браузеров...\n")
        logging.info("Запущена проверка версий браузеров")

        # Проверяем Chrome
        chrome_version = self.get_chrome_version()
        if chrome_version:
            latest_chrome = self.get_latest_chrome_version()
            self.browser_output.append(f"Google Chrome:\n- Текущая версия: {chrome_version}")
            self.browser_output.append(f"- Последняя версия: {latest_chrome}")

            if chrome_version != latest_chrome:
                self.browser_output.append("- Статус: Доступно обновление!")
            else:
                self.browser_output.append("- Статус: Установлена последняя версия")

            self.browser_output.append("")
        else:
            self.browser_output.append("Google Chrome не установлен\n")

        # Проверяем Opera
        opera_version = self.get_opera_version()
        if opera_version:
            latest_opera = self.get_latest_opera_version()
            self.browser_output.append(f"Opera:\n- Текущая версия: {opera_version}")
            self.browser_output.append(f"- Последняя версия: {latest_opera}")

            if opera_version != latest_opera:
                self.browser_output.append("- Статус: Доступно обновление!")
            else:
                self.browser_output.append("- Статус: Установлена последняя версия")

            self.browser_output.append("")
        else:
            self.browser_output.append("Opera не установлена\n")

        # Проверяем Edge
        edge_version = self.get_edge_version()
        if edge_version:
            latest_edge = self.get_latest_edge_version()
            self.browser_output.append(f"Microsoft Edge:\n- Текущая версия: {edge_version}")
            self.browser_output.append(f"- Последняя версия: {latest_edge}")

            if edge_version != latest_edge:
                self.browser_output.append("- Статус: Доступно обновление!")
            else:
                self.browser_output.append("- Статус: Установлена последняя версия")

            self.browser_output.append("")
        else:
            self.browser_output.append("Microsoft Edge не установлен\n")

        logging.info("Проверка версий браузеров завершена")

    def get_chrome_version(self):
        try:
            # Пытаемся найти Chrome в стандартных местах установки
            paths = [
                r'C:\Program Files\Google\Chrome\Application\chrome.exe',
                r'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe',
                os.path.expanduser('~') + r'\AppData\Local\Google\Chrome\Application\chrome.exe'
            ]

            for path in paths:
                if os.path.exists(path):
                    # Получаем версию из свойств файла
                    info = subprocess.check_output(
                        ['powershell', '-command', f'(Get-Item "{path}").VersionInfo.ProductVersion'],
                        text=True
                    )
                    version = info.strip()
                    logging.info(f"Обнаружен Chrome версии {version}")
                    return version

            # Или пытаемся найти в реестре
            try:
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                                     r'Software\Google\Chrome\BLBeacon')
                version, _ = winreg.QueryValueEx(key, 'version')
                winreg.CloseKey(key)
                return version
            except:
                pass

            logging.info("Chrome не обнаружен")
            return None
        except Exception as e:
            logging.error(f"Ошибка при определении версии Chrome: {str(e)}")
            return None

    def get_latest_chrome_version(self):
        try:
            # Получаем информацию о последней версии Chrome с сайта
            response = requests.get('https://chromedriver.storage.googleapis.com/LATEST_RELEASE')
            if response.status_code == 200:
                version = response.text.strip()
                logging.info(f"Последняя версия Chrome: {version}")
                return version
            return "Не удалось определить"
        except Exception as e:
            logging.error(f"Ошибка при получении последней версии Chrome: {str(e)}")
            return "Не удалось определить"

    def get_opera_version(self):
        try:
            # Пытаемся найти Opera в стандартных местах установки
            paths = [
                r'C:\Program Files\Opera\launcher.exe',
                r'C:\Program Files (x86)\Opera\launcher.exe',
                os.path.expanduser('~') + r'\AppData\Local\Programs\Opera\launcher.exe'
            ]

            for path in paths:
                if os.path.exists(path):
                    # Получаем версию из свойств файла
                    info = subprocess.check_output(
                        ['powershell', '-command', f'(Get-Item "{path}").VersionInfo.ProductVersion'],
                        text=True
                    )
                    version = info.strip()
                    logging.info(f"Обнаружена Opera версии {version}")
                    return version

            logging.info("Opera не обнаружена")
            return None
        except Exception as e:
            logging.error(f"Ошибка при определении версии Opera: {str(e)}")
            return None

    def get_latest_opera_version(self):
        try:
            # Получаем страницу Opera и ищем информацию о версии
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            response = requests.get('https://www.opera.com/download', headers=headers)

            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')

                # Пытаемся найти версию в тексте страницы
                version_text = soup.find('span', {'class': 'version'})
                if version_text:
                    version = version_text.text.strip()
                    logging.info(f"Последняя версия Opera: {version}")
                    return version

                # Альтернативный поиск
                version_match = re.search(r'Opera\s+(\d+\.\d+)', response.text)
                if version_match:
                    version = version_match.group(1)
                    logging.info(f"Последняя версия Opera: {version}")
                    return version

            return "Не удалось определить"
        except Exception as e:
            logging.error(f"Ошибка при получении последней версии Opera: {str(e)}")
            return "Не удалось определить"

    def get_edge_version(self):
        try:
            # Пытаемся найти Edge в стандартных местах установки
            paths = [
                r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe',
                r'C:\Program Files\Microsoft\Edge\Application\msedge.exe'
            ]

            for path in paths:
                if os.path.exists(path):
                    # Получаем версию из свойств файла
                    info = subprocess.check_output(
                        ['powershell', '-command', f'(Get-Item "{path}").VersionInfo.ProductVersion'],
                        text=True
                    )
                    version = info.strip()
                    logging.info(f"Обнаружен Edge версии {version}")
                    return version

            # Или пытаемся найти в реестре
            try:
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                                     r'Software\Microsoft\Edge\BLBeacon')
                version, _ = winreg.QueryValueEx(key, 'version')
                winreg.CloseKey(key)
                return version
            except:
                pass

            logging.info("Edge не обнаружен")
            return None
        except Exception as e:
            logging.error(f"Ошибка при определении версии Edge: {str(e)}")
            return None

    def get_latest_edge_version(self):
        try:
            # Получаем информацию о последней версии Edge
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            response = requests.get('https://www.microsoft.com/en-us/edge', headers=headers)

            if response.status_code == 200:
                # Пытаемся найти версию в тексте страницы
                version_match = re.search(r'Version\s+(\d+\.\d+\.\d+\.\d+)', response.text)
                if version_match:
                    version = version_match.group(1)
                    logging.info(f"Последняя версия Edge: {version}")
                    return version

            return "Не удалось определить"
        except Exception as e:
            logging.error(f"Ошибка при получении последней версии Edge: {str(e)}")
            return "Не удалось определить"

    def scan_system(self):
        self.progress_bar.setValue(0)
        self.system_output.clear()
        self.system_output.append("Начало сканирования системы...\n")
        logging.info("Запущено сканирование системы")

        # Создаем и запускаем поток для сканирования
        self.scan_thread = SystemScanThread()
        self.scan_thread.progress_update.connect(self.update_progress)
        self.scan_thread.scan_complete.connect(self.display_scan_results)
        self.scan_thread.start()

    def update_progress(self, value):
        self.progress_bar.setValue(value)

    def display_scan_results(self, results):
        self.system_output.append(results)
        self.system_output.append("\nСканирование завершено.")

    def open_url(self):
        url = self.url_input.text()

        # Проверяем валидность URL
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url

        try:
            # Открываем URL в браузере по умолчанию
            webbrowser.open(url)

            # Добавляем URL в историю
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            self.url_history.append(f"[{timestamp}] {url}")

            logging.info(f"Открыт URL: {url}")
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Не удалось открыть URL: {str(e)}")
            logging.error(f"Ошибка при открытии URL {url}: {str(e)}")

    def check_autostart(self):
        try:
            # Проверяем, есть ли приложение в автозапуске
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                                 r'Software\Microsoft\Windows\CurrentVersion\Run',
                                 0, winreg.KEY_READ)

            try:
                value, _ = winreg.QueryValueEx(key, 'BrowserCheckerApp')
                autostart_enabled = True
                logging.info("Автозапуск включен")
            except:
                autostart_enabled = False
                logging.info("Автозапуск выключен")

            winreg.CloseKey(key)
            return autostart_enabled
        except Exception as e:
            logging.error(f"Ошибка при проверке автозапуска: {str(e)}")
            return False

    def toggle_autostart(self):
        try:
            app_path = sys.argv[0]
            app_path = os.path.abspath(app_path)

            # Открываем ключ реестра для автозапуска
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                                 r'Software\Microsoft\Windows\CurrentVersion\Run',
                                 0, winreg.KEY_ALL_ACCESS)

            if self.check_autostart():
                # Удаляем из автозапуска
                winreg.DeleteValue(key, 'BrowserCheckerApp')
                QMessageBox.information(self, "Автозапуск", "Автозапуск отключен")
                logging.info("Автозапуск отключен")
            else:
                # Добавляем в автозапуск
                winreg.SetValueEx(key, 'BrowserCheckerApp', 0, winreg.REG_SZ, f'"{app_path}"')
                QMessageBox.information(self, "Автозапуск", "Автозапуск включен")
                logging.info("Автозапуск включен")

            winreg.CloseKey(key)
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Не удалось изменить настройки автозапуска: {str(e)}")
            logging.error(f"Ошибка при изменении настроек автозапуска: {str(e)}")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = BrowserCheckerApp()
    window.show()
    sys.exit(app.exec_())