import os
import subprocess
from pyngrok import ngrok

try:
    from google.colab import drive

    colab_env = True
except ImportError:
    colab_env = False


EXTENSIONS = ["ms-python.python", "ms-toolsai.jupyter"]


class ColabCode:
    def __init__(self, workspace, port=10000, password=None, authtoken=None, mount_drive=False, user_data_dir=None, extensions_dir=None):
        self.workspace = workspace
        self.port = port
        self.password = password
        self.authtoken = authtoken
        self.user_data_dir = user_data_dir
        self.extensions_dir = extensions_dir

        self._mount = mount_drive
        self._install_code()
        self._install_extensions()
        self._start_server()
        self._run_code()

    def _install_code(self):
        subprocess.run(
            ["wget", "https://code-server.dev/install.sh"], stdout=subprocess.PIPE
        )
        subprocess.run(["sh", "install.sh"], stdout=subprocess.PIPE)

    def _install_extensions(self):
        for ext in EXTENSIONS:
            subprocess.run(["code-server", "--install-extension", f"{ext}"])

    def _start_server(self):
        if self.authtoken:
            ngrok.set_auth_token(self.authtoken)
        active_tunnels = ngrok.get_tunnels()
        for tunnel in active_tunnels:
            public_url = tunnel.public_url
            ngrok.disconnect(public_url)
        url = ngrok.connect(addr=self.port, options={"bind_tls": True})
        print(f"Code Server can be accessed on: {url}")

    def _run_code(self):
        os.system(f"fuser -n tcp -k {self.port}")
        if self._mount and colab_env:
            drive.mount("/content/drive")

        prefix, options = [], [f"--port {self.port}", "--disable-telemetry"]
        if self.password:
            prefix.append(f"PASSWORD={self.password}")
        else:
            options.append("--auth none")

        if self.user_data_dir:
            options.append(f"--user-data-dir {self.user_data_dir}")

        if self.extensions_dir:
            options.append(f"--extensions-dir {self.extensions_dir}")

        options_str = " ".join(options)
        code_cmd = f"{prefix} code-server {options_str} {self.workspace}"
        print(code_cmd)

        with subprocess.Popen(
            [code_cmd],
            shell=True,
            stdout=subprocess.PIPE,
            bufsize=1,
            universal_newlines=True,
        ) as proc:
            for line in proc.stdout:
                print(line, end="")
