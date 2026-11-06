"""Baixa ferramentas locais e valida seus checksums oficiais; não altera o PATH."""
import hashlib
import os
from pathlib import Path
import platform
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / '.tools'


def download(url):
    with urllib.request.urlopen(url, timeout=120) as response:
        return response.read()


def main():
    system = platform.system().lower()
    machine = platform.machine().lower()
    arch = {'amd64': 'amd64', 'x86_64': 'amd64', 'arm64': 'arm64', 'aarch64': 'arm64'}.get(machine)
    if system not in ('windows', 'linux', 'darwin') or arch is None:
        raise RuntimeError('Plataforma não suportada automaticamente')
    DEST.mkdir(exist_ok=True)
    suffix = '.exe' if system == 'windows' else ''
    kind = f'https://github.com/kubernetes-sigs/kind/releases/download/v0.33.0/kind-{system}-{arch}'
    kubectl = f'https://dl.k8s.io/release/v1.35.5/bin/{system}/{arch}/kubectl{suffix}'
    for name, url, checksum_url in [('kind', kind, kind + '.sha256sum'), ('kubectl', kubectl, kubectl + '.sha256')]:
        expected = download(checksum_url).decode().split()[0]
        payload = download(url)
        if hashlib.sha256(payload).hexdigest() != expected:
            raise RuntimeError('Checksum inválido: ' + name)
        target = DEST / (name + suffix)
        target.write_bytes(payload)
        if os.name != 'nt':
            target.chmod(0o755)
        print(name + ': checksum validado')


if __name__ == '__main__':
    main()
