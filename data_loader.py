import io
from ftplib import FTP

import pandas as pd
import streamlit as st


def _get_ftp_config():
    ftp_cfg = st.secrets["ftp"] if "ftp" in st.secrets else st.secrets
    required_keys = ["host", "username", "password", "remote_dir"]
    missing_keys = [key for key in required_keys if key not in ftp_cfg or not str(ftp_cfg[key]).strip()]
    if missing_keys:
        st.error(
            "Missing FTP configuration. Provide either [ftp] with host/username/password/remote_dir "
            f"or top-level keys. Missing: {', '.join(missing_keys)}"
        )
        st.stop()

    return {key: str(ftp_cfg[key]).strip() for key in required_keys}


@st.cache_data(show_spinner=False)
def fetch_csv_bytes(filename: str) -> bytes:
    ftp_cfg = _get_ftp_config()

    try:
        with FTP(ftp_cfg["host"], timeout=30) as ftp:
            ftp.login(user=ftp_cfg["username"], passwd=ftp_cfg["password"])
            ftp.cwd(ftp_cfg["remote_dir"])

            buffer = io.BytesIO()
            ftp.retrbinary(f"RETR {filename}", buffer.write)
            buffer.seek(0)
            return buffer.getvalue()
    except Exception as exc:
        st.error(
            "FTP read failed. Verify host/username/password and remote_dir in Streamlit Secrets. "
            f"Tried remote_dir='{ftp_cfg['remote_dir']}' and file='{filename}'."
        )
        raise RuntimeError(f"FTP fetch failed for {filename}: {exc}") from exc


def load_csv_from_ftp(filename: str, encoding: str = "latin-1", **read_csv_kwargs) -> pd.DataFrame:
    csv_bytes = fetch_csv_bytes(filename)
    return pd.read_csv(io.BytesIO(csv_bytes), encoding=encoding, **read_csv_kwargs)
