import os
import sys
import winreg
import subprocess
import requests
import re
import logging
import webbrowser
import platform
import json
from datetime import datetime
from bs4 import BeautifulSoup
from flask import Flask, render_template, request, jsonify, redirect, url_for, session

# Настройка логирования
logging.basicConfig(
    filename='browser_checker.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

app = Flask(__name__)
app.secret_key = 'browser_checker_secret_key'  # Для работы с сессиями

# Хранилище для истории URL
url_history = []


# Функции для проверки браузеров
def get_chrome_version():
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


def get_latest_chrome_version():
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


def get_opera_version():
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


def get_latest_opera_version():
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


def get_edge_version():
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


def get_latest_edge_version():
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


def scan_system():
    try:
        result = {}

        # Информация о системе
        result['os'] = {
            'system': platform.system(),
            'release': platform.release(),
            'version': platform.version(),
            'architecture': platform.machine(),
            'processor': platform.processor()
        }

        # Информация о памяти (только для Windows)
        if platform.system() == 'Windows':
            try:
                mem_info = subprocess.check_output(['systeminfo'], text=True)
                physical_memory = re.search(r'Total Physical Memory:\s*([\d,]+)', mem_info)
                if physical_memory:
                    result['memory'] = physical_memory.group(1)
                else:
                    result['memory'] = "Не удалось определить"
            except:
                result['memory'] = "Не удалось определить"

        # Список запущенных процессов
        if platform.system() == 'Windows':
            try:
                processes = subprocess.check_output(['tasklist'], text=True)
                top_processes = processes.split('\n')[:20]
                result['processes'] = top_processes
            except:
                result['processes'] = ["Не удалось получить список процессов"]

        # Информация о дисках
        if platform.system() == 'Windows':
            try:
                drives = subprocess.check_output(['wmic', 'logicaldisk', 'get', 'caption,freespace,size,volumename'],
                                                 text=True)
                drive_lines = drives.strip().split('\n')
                result['drives'] = drive_lines
            except:
                result['drives'] = ["Не удалось получить информацию о дисках"]

        logging.info("Сканирование системы выполнено успешно")
        return result

    except Exception as e:
        logging.error(f"Ошибка при сканировании системы: {str(e)}")
        return {"error": str(e)}


def check_autostart():
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


def toggle_autostart():
    try:
        app_path = sys.argv[0]
        app_path = os.path.abspath(app_path)

        # Открываем ключ реестра для автозапуска
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                             r'Software\Microsoft\Windows\CurrentVersion\Run',
                             0, winreg.KEY_ALL_ACCESS)

        if check_autostart():
            # Удаляем из автозапуска
            winreg.DeleteValue(key, 'BrowserCheckerApp')
            message = "Автозапуск отключен"
            logging.info("Автозапуск отключен")
        else:
            # Добавляем в автозапуск
            winreg.SetValueEx(key, 'BrowserCheckerApp', 0, winreg.REG_SZ, f'"{app_path}"')
            message = "Автозапуск включен"
            logging.info("Автозапуск включен")

        winreg.CloseKey(key)
        return {"success": True, "message": message}
    except Exception as e:
        logging.error(f"Ошибка при изменении настроек автозапуска: {str(e)}")
        return {"success": False, "message": f"Ошибка: {str(e)}"}


# Маршруты Flask
@app.route('/')
def index():
    return render_template('index.html')


@app.route('/check_browsers', methods=['GET'])
def check_browsers():
    results = {}

    # Проверяем Chrome
    chrome_version = get_chrome_version()
    if chrome_version:
        latest_chrome = get_latest_chrome_version()
        results['chrome'] = {
            'installed': True,
            'current_version': chrome_version,
            'latest_version': latest_chrome,
            'needs_update': chrome_version != latest_chrome and latest_chrome != 'Не удалось определить'
        }
    else:
        results['chrome'] = {'installed': False}

    # Проверяем Opera
    opera_version = get_opera_version()
    if opera_version:
        latest_opera = get_latest_opera_version()
        results['opera'] = {
            'installed': True,
            'current_version': opera_version,
            'latest_version': latest_opera,
            'needs_update': opera_version != latest_opera and latest_opera != 'Не удалось определить'
        }
    else:
        results['opera'] = {'installed': False}

    # Проверяем Edge
    edge_version = get_edge_version()
    if edge_version:
        latest_edge = get_latest_edge_version()
        results['edge'] = {
            'installed': True,
            'current_version': edge_version,
            'latest_version': latest_edge,
            'needs_update': edge_version != latest_edge and latest_edge != 'Не удалось определить'
        }
    else:
        results['edge'] = {'installed': False}

    logging.info("Выполнена проверка версий браузеров")
    return jsonify(results)


@app.route('/scan_system', methods=['GET'])
def scan_system_route():
    result = scan_system()
    return jsonify(result)


@app.route('/check_autostart', methods=['GET'])
def check_autostart_route():
    enabled = check_autostart()
    return jsonify({'enabled': enabled})


@app.route('/toggle_autostart', methods=['POST'])
def toggle_autostart_route():
    result = toggle_autostart()
    return jsonify(result)


@app.route('/open_url', methods=['POST'])
def open_url():
    data = request.get_json()
    url = data.get('url', '')

    # Проверяем валидность URL
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url

    try:
        # Открываем URL в браузере по умолчанию
        webbrowser.open(url)

        # Добавляем URL в историю
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        url_entry = {
            'url': url,
            'timestamp': timestamp
        }
        url_history.append(url_entry)

        # Ограничиваем историю до 100 записей
        if len(url_history) > 100:
            url_history.pop(0)

        logging.info(f"Открыт URL: {url}")
        return jsonify({'success': True})
    except Exception as e:
        logging.error(f"Ошибка при открытии URL {url}: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})


@app.route('/get_url_history', methods=['GET'])
def get_url_history():
    return jsonify(url_history)


# Дополнительный маршрут для отслеживания запуска
@app.route('/log_startup', methods=['POST'])
def log_startup():
    logging.info("Веб-приложение запущено")
    return jsonify({'success': True})


os.makedirs('templates', exist_ok=True)
with open('templates/index.html', 'w', encoding='utf-8') as f:
    f.write('''<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Проверка браузеров</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body {
            padding-top: 20px;
            padding-bottom: 20px;
        }
        .tab-content {
            padding: 20px;
            border: 1px solid #dee2e6;
            border-top: none;
            border-radius: 0 0 5px 5px;
        }
        .status-ok {
            color: green;
            font-weight: bold;
        }
        .status-update {
            color: red;
            font-weight: bold;
        }
        .progress {
            margin-top: 10px;
            margin-bottom: 20px;
        }
        .badge {
            margin-left: 5px;
        }
        .system-info {
            max-height: 500px;
            overflow-y: auto;
        }
        #urlHistory {
            max-height: 300px;
            overflow-y: auto;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1 class="text-center mb-4">Проверка браузеров и система</h1>

        <ul class="nav nav-tabs" id="mainTab" role="tablist">
            <li class="nav-item" role="presentation">
                <button class="nav-link active" id="browsers-tab" data-bs-toggle="tab" data-bs-target="#browsers" type="button" role="tab" aria-controls="browsers" aria-selected="true">Браузеры</button>
            </li>
            <li class="nav-item" role="presentation">
                <button class="nav-link" id="system-tab" data-bs-toggle="tab" data-bs-target="#system" type="button" role="tab" aria-controls="system" aria-selected="false">Сканирование системы</button>
            </li>
            <li class="nav-item" role="presentation">
                <button class="nav-link" id="url-tab" data-bs-toggle="tab" data-bs-target="#url" type="button" role="tab" aria-controls="url" aria-selected="false">Открытие URL</button>
            </li>
        </ul>

        <div class="tab-content" id="mainTabContent">
            <!-- Вкладка браузеров -->
            <div class="tab-pane fade show active" id="browsers" role="tabpanel" aria-labelledby="browsers-tab">
                <div class="mb-3">
                    <button id="checkBrowsersBtn" class="btn btn-primary">Проверить версии браузеров</button>
                    <button id="toggleAutostartBtn" class="btn btn-secondary ms-2">Включить/Выключить автозапуск</button>
                    <span id="autostartStatus" class="ms-2 badge rounded-pill"></span>
                </div>

                <div class="card mb-3">
                    <div class="card-header">
                        <h5>Google Chrome</h5>
                    </div>
                    <div class="card-body" id="chromeResult">
                        <p>Нажмите кнопку "Проверить версии браузеров" для получения информации.</p>
                    </div>
                </div>

                <div class="card mb-3">
                    <div class="card-header">
                        <h5>Opera</h5>
                    </div>
                    <div class="card-body" id="operaResult">
                        <p>Нажмите кнопку "Проверить версии браузеров" для получения информации.</p>
                    </div>
                </div>

                <div class="card">
                    <div class="card-header">
                        <h5>Microsoft Edge</h5>
                    </div>
                    <div class="card-body" id="edgeResult">
                        <p>Нажмите кнопку "Проверить версии браузеров" для получения информации.</p>
                    </div>
                </div>
            </div>

            <!-- Вкладка сканирования системы -->
            <div class="tab-pane fade" id="system" role="tabpanel" aria-labelledby="system-tab">
                <button id="scanSystemBtn" class="btn btn-primary mb-3">Сканировать систему</button>

                <div class="progress mb-4" style="display: none;" id="scanProgress">
                    <div class="progress-bar progress-bar-striped progress-bar-animated" role="progressbar" aria-valuenow="100" aria-valuemin="0" aria-valuemax="100" style="width: 100%"></div>
                </div>

                <div class="system-info" id="systemResult">
                    <p>Нажмите кнопку "Сканировать систему" для получения информации.</p>
                </div>
            </div>

            <!-- Вкладка открытия URL -->
            <div class="tab-pane fade" id="url" role="tabpanel" aria-labelledby="url-tab">
                <div class="input-group mb-3">
                    <input type="text" class="form-control" id="urlInput" placeholder="https://example.com" value="https://">
                    <button class="btn btn-primary" id="openUrlBtn">Открыть URL</button>
                </div>

                <div class="card">
                    <div class="card-header">
                        <h5>История</h5>
                    </div>
                    <div class="card-body">
                        <div id="urlHistory" class="list-group">
                            <!-- История URL будет отображаться здесь -->
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        document.addEventListener('DOMContentLoaded', function() {
            // Логирование запуска приложения
            fetch('/log_startup', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            // Проверка автозапуска при старте
            checkAutostart();

            // Обработчики событий для кнопок
            document.getElementById('checkBrowsersBtn').addEventListener('click', checkBrowsers);
            document.getElementById('toggleAutostartBtn').addEventListener('click', toggleAutostart);
            document.getElementById('scanSystemBtn').addEventListener('click', scanSystem);
            document.getElementById('openUrlBtn').addEventListener('click', openUrl);

            // Загрузка истории URL
            loadUrlHistory();
        });

        // Функция проверки статуса автозапуска
        function checkAutostart() {
            fetch('/check_autostart')
                .then(response => response.json())
                .then(data => {
                    const statusBadge = document.getElementById('autostartStatus');
                    if (data.enabled) {
                        statusBadge.textContent = 'Автозапуск включен';
                        statusBadge.classList.add('bg-success');
                        statusBadge.classList.remove('bg-secondary');
                    } else {
                        statusBadge.textContent = 'Автозапуск выключен';
                        statusBadge.classList.add('bg-secondary');
                        statusBadge.classList.remove('bg-success');
                    }
                })
                .catch(error => {
                    console.error('Ошибка при проверке автозапуска:', error);
                });
        }

        // Функция включения/выключения автозапуска
        function toggleAutostart() {
            fetch('/toggle_autostart', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        alert(data.message);
                        checkAutostart(); // Обновляем статус
                    } else {
                        alert('Ошибка: ' + data.message);
                    }
                })
                .catch(error => {
                    console.error('Ошибка при изменении автозапуска:', error);
                    alert('Ошибка при изменении автозапуска: ' + error);
                });
        }

        // Функция проверки версий браузеров
        function checkBrowsers() {
            document.getElementById('chromeResult').innerHTML = '<p>Загрузка информации...</p>';
            document.getElementById('operaResult').innerHTML = '<p>Загрузка информации...</p>';
            document.getElementById('edgeResult').innerHTML = '<p>Загрузка информации...</p>';

            fetch('/check_browsers')
                .then(response => response.json())
                .then(data => {
                    // Chrome
                    const chromeResult = document.getElementById('chromeResult');
                    if (data.chrome.installed) {
                        let chromeStatus = data.chrome.needs_update ? 
                            '<span class="status-update">Доступно обновление!</span>' : 
                            '<span class="status-ok">Установлена последняя версия</span>';

                        chromeResult.innerHTML = `
                            <p><strong>Текущая версия:</strong> ${data.chrome.current_version}</p>
                            <p><strong>Последняя версия:</strong> ${data.chrome.latest_version}</p>
                            <p><strong>Статус:</strong> ${chromeStatus}</p>
                        `;
                    } else {
                        chromeResult.innerHTML = '<p>Google Chrome не установлен</p>';
                    }

                    // Opera
                    const operaResult = document.getElementById('operaResult');
                    if (data.opera.installed) {
                        let operaStatus = data.opera.needs_update ? 
                            '<span class="status-update">Доступно обновление!</span>' : 
                            '<span class="status-ok">Установлена последняя версия</span>';

                        operaResult.innerHTML = `
                            <p><strong>Текущая версия:</strong> ${data.opera.current_version}</p>
                            <p><strong>Последняя версия:</strong> ${data.opera.latest_version}</p>
                            <p><strong>Статус:</strong> ${operaStatus}</p>
                        `;
                    } else {
                        operaResult.innerHTML = '<p>Opera не установлена</p>';
                    }

                    // Edge
                    const edgeResult = document.getElementById('edgeResult');
                    if (data.edge.installed) {
                        let edgeStatus = data.edge.needs_update ? 
                            '<span class="status-update">Доступно обновление!</span>' : 
                            '<span class="status-ok">Установлена последняя версия</span>';

                        edgeResult.innerHTML = `
                            <p><strong>Текущая версия:</strong> ${data.edge.current_version}</p>
                            <p><strong>Последняя версия:</strong> ${data.edge.latest_version}</p>
                            <p><strong>Статус:</strong> ${edgeStatus}</p>
                        `;
                    } else {
                        edgeResult.innerHTML = '<p>Microsoft Edge не установлен</p>';
                    }
                })
                .catch(error => {
                    console.error('Ошибка при проверке браузеров:', error);
                    document.getElementById('chromeResult').innerHTML = '<p>Ошибка при получении информации</p>';
                    document.getElementById('operaResult').innerHTML = '<p>Ошибка при получении информации</p>';
                    document.getElementById('edgeResult').innerHTML = '<p>Ошибка при получении информации</p>';
                });
        }

        // Функция сканирования системы
        function scanSystem() {
            const systemResult = document.getElementById('systemResult');
            const progressBar = document.getElementById('scanProgress');

            systemResult.innerHTML = '<p>Выполняется сканирование...</p>';
            progressBar.style.display = 'block';

            fetch('/scan_system')
                .then(response => response.json())
                .then(data => {
                    progressBar.style.display = 'none';

                    if (data.error) {
                        systemResult.innerHTML = `<p>Ошибка при сканировании: ${data.error}</p>`;
                        return;
                    }

                    let result = '<h4>Информация о системе</h4>';
                    result += `<p><strong>Операционная система:</strong> ${data.os.system} ${data.os.release}</p>`;
                    result += `<p><strong>Версия:</strong> ${data.os.version}</p>`;
                    result += `<p><strong>Архитектура:</strong> ${data.os.architecture}</p>`;
                    result += `<p><strong>Процессор:</strong> ${data.os.processor}</p>`;

                    if (data.memory) {
                        result += `<p><strong>Оперативная память:</strong> ${data.memory}</p>`;
                    }

                    if (data.processes && data.processes.length > 0) {
                        result += '<h4>Запущенные процессы</h4>';
                        result += '<pre class="bg-light p-2">';
                        result += data.processes.join('\\n');
                        result += '</pre>';
                    }

                    if (data.drives && data.drives.length > 0) {
                        result += '<h4>Информация о дисках</h4>';
                        result += '<pre class="bg-light p-2">';
                        result += data.drives.join('\\n');
                        result += '</pre>';
                    }

                    systemResult.innerHTML = result;
                })
                .catch(error => {
                    console.error('Ошибка при сканировании системы:', error);
                    progressBar.style.display = 'none';
                    systemResult.innerHTML = '<p>Ошибка при сканировании системы</p>';
                });
        }
        
        // Функция открытия URL
        function openUrl() {
            const urlInput = document.getElementById('urlInput');
            const url = urlInput.value.trim();
            
            if (!url) {
                alert('Введите URL для открытия');
                return;
            }
            
            fetch('/open_url', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ url: url })
            })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        // Обновляем историю URL после успешного открытия
                        loadUrlHistory();
                    } else {
                        alert('Ошибка при открытии URL: ' + data.error);
                    }
                })
                .catch(error => {
                    console.error('Ошибка при открытии URL:', error);
                    alert('Ошибка при открытии URL: ' + error);
                });
        }
        
        // Функция загрузки истории URL
        function loadUrlHistory() {
            fetch('/get_url_history')
                .then(response => response.json())
                .then(data => {
                    const historyContainer = document.getElementById('urlHistory');
                    historyContainer.innerHTML = '';
                    
                    if (data.length === 0) {
                        historyContainer.innerHTML = '<p class="text-muted">История пуста</p>';
                        return;
                    }
                    
                    // Отображаем историю в обратном порядке (новые сверху)
                    data.reverse().forEach(item => {
                        const historyItem = document.createElement('a');
                        historyItem.href = '#';
                        historyItem.className = 'list-group-item list-group-item-action';
                        historyItem.innerHTML = `
                            <div class="d-flex w-100 justify-content-between">
                                <h6 class="mb-1">${item.url}</h6>
                                <small>${item.timestamp}</small>
                            </div>
                        `;
                        
                        // Клик по элементу истории заполняет поле ввода
                        historyItem.addEventListener('click', function(e) {
                            e.preventDefault();
                            document.getElementById('urlInput').value = item.url;
                        });
                        
                        historyContainer.appendChild(historyItem);
                    });
                })
                .catch(error => {
                    console.error('Ошибка при загрузке истории URL:', error);
                    document.getElementById('urlHistory').innerHTML = '<p>Ошибка при загрузке истории</p>';
                });
        }
    </script>
</body>
</html>''')

if __name__ == '__main__':
    try:
        # Создаем логирование с текущей датой
        current_date = datetime.now().strftime('%Y-%m-%d')
        log_file = f'browser_checker_{current_date}.log'

        # Настраиваем логирование
        logging.basicConfig(
            filename=log_file,
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )

        logging.info("Start")

        # Запускаем Flask-приложение
        app.run(debug=False, port=5000)
    except Exception as e:
        logging.error(f"Критическая ошибка при запуске приложения: {str(e)}")
        print(f"Ошибка: {str(e)}")

        #http://localhost:5000