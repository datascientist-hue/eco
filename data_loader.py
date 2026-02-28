import io
from pathlib import PurePosixPath
from ftplib import FTP

import pandas as pd
import streamlit as st


def _get_ftp_config():
    ftp_cfg = st.secrets["ftp"] if "ftp" in st.secrets else st.secrets
    alias_map = {
        "host": ["host", "hostname", "server"],
        "username": ["username", "user", "user_name", "login"],
        "password": ["password", "pass", "pwd"],
        "remote_dir": ["remote_dir", "remoteDir", "remote_path", "path", "directory"],
    }
    file_path_keys = [
        "inventory",
        "open_po",
        "open_so",
        "overdue",
        "overdue_creditor",
        "overdue_payment",
        "stock_status",
    ]

    normalized_cfg = {}
    missing_keys = []
    for required_key, aliases in alias_map.items():
        value = None
        for alias in aliases:
            if alias in ftp_cfg and str(ftp_cfg[alias]).strip():
                value = str(ftp_cfg[alias]).strip()
                break

        if required_key == "remote_dir" and value is None:
            for key_name in file_path_keys:
                if key_name in ftp_cfg and str(ftp_cfg[key_name]).strip():
                    candidate = str(ftp_cfg[key_name]).strip()
                    parent_dir = str(PurePosixPath(candidate).parent)
                    if parent_dir and parent_dir != ".":
                        value = parent_dir
                        break

        if value is None:
            missing_keys.append(required_key)
        else:
            normalized_cfg[required_key] = value

    if missing_keys:
        available_keys = ", ".join(sorted([str(k) for k in ftp_cfg.keys()])) if hasattr(ftp_cfg, "keys") else "none"
        st.error(
            "Missing FTP configuration. Provide either [ftp] with host/username/password/remote_dir "
            f"or top-level keys. Missing: {', '.join(missing_keys)}. Found keys: {available_keys}"
        )
        st.stop()

    return normalized_cfg


@st.cache_data(show_spinner=False)
def fetch_csv_bytes(filename: str) -> bytes:
    ftp_cfg = _get_ftp_config()
    file_name_only = PurePosixPath(str(filename)).name

    try:
        with FTP(ftp_cfg["host"], timeout=30) as ftp:
            ftp.login(user=ftp_cfg["username"], passwd=ftp_cfg["password"])
            ftp.set_pasv(True)
            ftp.cwd(ftp_cfg["remote_dir"])

            buffer = io.BytesIO()
            ftp.retrbinary(f"RETR {file_name_only}", buffer.write)
            buffer.seek(0)
            return buffer.getvalue()
    except Exception as exc:
        st.error(
            "FTP read failed. Verify host/username/password and remote_dir in Streamlit Secrets. "
            f"Tried remote_dir='{ftp_cfg['remote_dir']}' and file='{file_name_only}'. Error: {exc}"
        )
        st.stop()


def load_csv_from_ftp(filename: str, encoding: str = "latin-1", **read_csv_kwargs) -> pd.DataFrame:
    csv_bytes = fetch_csv_bytes(filename)
    return pd.read_csv(io.BytesIO(csv_bytes), encoding=encoding, **read_csv_kwargs)
