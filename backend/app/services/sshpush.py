import paramiko


JUNOS_CFG_ENTER = "configure\n"
JUNOS_LOAD_SET = "load set terminal\n"
JUNOS_SHOW_COMPARE = "show | compare\n"
JUNOS_COMMIT = "commit and-quit\n"
JUNOS_QUIT = "quit\n"


def _connect(host, username, password, private_key_path=None):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    if private_key_path:
        key = paramiko.RSAKey.from_private_key_file(private_key_path)
        client.connect(host, username=username, pkey=key, look_for_keys=False)
    else:
        client.connect(host, username=username, password=password, look_for_keys=False)
    return client


def push_juniper_set_config(host: str, username: str, password: str, private_key_path: str | None, config_text: str, dry_run: bool):
    """Push set-style config lines to JunOS using an interactive shell.
    For dry_run=True, returns the diff without commit.
    """
    client = _connect(host, username, password, private_key_path)
    chan = client.invoke_shell()


    def send(cmd):
        chan.send(cmd)
        while not chan.recv_ready():
            pass
        return chan.recv(65535).decode(errors="ignore")


    try:
        out = send(JUNOS_CFG_ENTER)
        out += send(JUNOS_LOAD_SET)
        # send config lines, terminate with Ctrl-D (EOF) to end 'load set terminal'
        for line in config_text.strip().splitlines():
            if line.strip():
                out += send(line + "\n")
        chan.send("\x04") # Ctrl-D
        while not chan.recv_ready():
            pass
        out += chan.recv(65535).decode(errors="ignore")


        out += send(JUNOS_SHOW_COMPARE)
        if dry_run:
            out += send(JUNOS_QUIT)
        else:
            out += send(JUNOS_COMMIT)
        return {"ok": True, "dry_run": dry_run, "output": out}
    finally:
        chan.close()
        client.close()