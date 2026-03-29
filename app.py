from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd
import streamlit as st


DATA_DIR = Path("data")


@dataclass
class LazarusData:
    demographics: pd.DataFrame
    telemetry: pd.DataFrame
    prescriptions: pd.DataFrame


def find_existing_file(candidates: Iterable[str]) -> Path | None:
    for name in candidates:
        path = DATA_DIR / name
        if path.exists():
            return path
    return None


def read_csv_loose(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, encoding_errors="ignore")


def load_lazarus_data() -> LazarusData:
    demo_file = find_existing_file(
        [
            "patient_demographics.csv",
            "patient_demographics.xlsx.csv",
            "patient_demographics_data.csv",
        ]
    )
    telem_file = find_existing_file(
        [
            "telemetry_logs.csv",
            "telemetry_log.csv",
            "telemetry.csv",
        ]
    )
    rx_file = find_existing_file(
        [
            "prescription_audit.csv",
            "prescriptions.csv",
            "pharmacy_audit.csv",
        ]
    )

    missing = [
        name
        for name, p in [
            ("patient_demographics", demo_file),
            ("telemetry_logs", telem_file),
            ("prescription_audit", rx_file),
        ]
        if p is None
    ]
    if missing:
        raise FileNotFoundError(
            "Missing required file(s): " + ", ".join(missing) + ". Place CSVs in ./data"
        )

    return LazarusData(
        demographics=read_csv_loose(demo_file),
        telemetry=read_csv_loose(telem_file),
        prescriptions=read_csv_loose(rx_file),
    )


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    copy = df.copy()
    copy.columns = [str(c).strip().lower().replace(" ", "_") for c in copy.columns]
    return copy


def choose_col(df: pd.DataFrame, options: list[str]) -> str | None:
    cols = set(df.columns)
    for opt in options:
        if opt in cols:
            return opt
    return None


def parse_id(raw: object) -> float:
    if pd.isna(raw):
        return np.nan
    text = str(raw)
    digits = "".join(ch for ch in text if ch.isdigit())
    if not digits:
        return np.nan
    return float(digits)


def ward_from_id(pid: object) -> str:
    n = parse_id(pid)
    if pd.isna(n):
        return "Unknown"
    return "Ward-EVEN" if int(n) % 2 == 0 else "Ward-ODD"


def caesar_shift(text: str, shift: int) -> str:
    result = []
    for ch in text:
        if "a" <= ch <= "z":
            idx = ord(ch) - ord("a")
            result.append(chr(ord("a") + ((idx + shift) % 26)))
        elif "A" <= ch <= "Z":
            idx = ord(ch) - ord("A")
            result.append(chr(ord("A") + ((idx + shift) % 26)))
        else:
            result.append(ch)
    return "".join(result)


def decrypt_med(scrambled: str, age: float | int | None) -> str:
    if pd.isna(scrambled):
        return ""
    text = str(scrambled)
    if age is None or pd.isna(age):
        shift = -13
    else:
        age_num = pd.to_numeric(age, errors="coerce")
        if pd.isna(age_num):
            shift = -13
        else:
            shift = -(int(age_num) % 26)
    return caesar_shift(text, shift)


def parse_hex_or_num(raw: object) -> float:
    if pd.isna(raw):
        return np.nan
    s = str(raw).strip().lower()
    if not s:
        return np.nan
    if s.startswith("0x"):
        try:
            return float(int(s, 16))
        except ValueError:
            return np.nan
    if all(ch in "0123456789abcdef" for ch in s) and any(ch.isalpha() for ch in s):
        try:
            return float(int(s, 16))
        except ValueError:
            pass
    try:
        return float(s)
    except ValueError:
        return np.nan


def normalize_patient_id(raw: object) -> str | None:
    if pd.isna(raw):
        return None
    text = str(raw).strip()
    if not text:
        return None
    parsed = parse_id(text)
    if not pd.isna(parsed):
        return str(int(parsed))
    return text


def prepare_identity_cards(df_demo: pd.DataFrame) -> pd.DataFrame:
    d = normalize_columns(df_demo)
    id_col = choose_col(d, ["patient_id", "id", "patient_code", "subject_id"])
    name_col = choose_col(d, ["decoded_name", "name", "patient_name", "full_name"])
    age_col = choose_col(d, ["age", "patient_age"])
    encoded_name_col = choose_col(d, ["encoded_name", "scrambled_name", "cipher_name"])

    if name_col is None and encoded_name_col is not None:
        d["decoded_name"] = d[encoded_name_col].astype(str).apply(lambda s: caesar_shift(s, -13))
        name_col = "decoded_name"

    if name_col is None:
        d["decoded_name"] = "Unknown"
        name_col = "decoded_name"

    if age_col is None:
        d["age"] = np.nan
        age_col = "age"

    if id_col is None:
        d["patient_id"] = np.arange(1, len(d) + 1)
        id_col = "patient_id"

    out = d[[id_col, name_col, age_col]].copy()
    out.columns = ["patient_id", "decoded_name", "age"]
    out["ward"] = out["patient_id"].apply(ward_from_id)
    return out


def prepare_telemetry(df_telem: pd.DataFrame) -> pd.DataFrame:
    t = normalize_columns(df_telem)
    id_col = choose_col(t, ["patient_id", "id", "subject_id", "patient_code"])
    ts_col = choose_col(t, ["timestamp", "time", "recorded_at", "ts"])
    bpm_col = choose_col(t, ["bpm", "heart_rate", "hr", "bpm_hex"])
    o2_col = choose_col(t, ["oxygen", "spo2", "o2", "oxygen_hex"])

    if id_col is None:
        t["patient_id"] = 1
        id_col = "patient_id"
    if ts_col is None:
        t["timestamp"] = pd.date_range("2026-01-01", periods=len(t), freq="min")
        ts_col = "timestamp"
    if bpm_col is None:
        t["bpm"] = np.nan
        bpm_col = "bpm"
    if o2_col is None:
        t["oxygen"] = np.nan
        o2_col = "oxygen"

    out = t[[id_col, ts_col, bpm_col, o2_col]].copy()
    out.columns = ["patient_id", "timestamp", "raw_bpm", "raw_oxygen"]
    out["timestamp"] = pd.to_datetime(out["timestamp"], errors="coerce")
    out["decoded_bpm"] = out["raw_bpm"].apply(parse_hex_or_num)
    out["decoded_oxygen"] = out["raw_oxygen"].apply(parse_hex_or_num)

    out = out.sort_values(["patient_id", "timestamp"], na_position="last")
    out["interpolated_oxygen"] = (
        out.groupby("patient_id", dropna=False)["decoded_oxygen"]
        .transform(lambda s: s.interpolate(limit_direction="both"))
        .clip(lower=50, upper=100)
    )
    return out


def prepare_pharmacy(df_rx: pd.DataFrame, identity: pd.DataFrame) -> pd.DataFrame:
    r = normalize_columns(df_rx)
    id_col = choose_col(r, ["patient_id", "id", "subject_id", "patient_code"])
    med_col = choose_col(r, ["scrambled_meds", "medication", "med", "drug", "cipher_med"])

    if id_col is None:
        r["patient_id"] = np.nan
        id_col = "patient_id"
    if med_col is None:
        r["scrambled_meds"] = ""
        med_col = "scrambled_meds"

    merged = r[[id_col, med_col]].copy()
    merged.columns = ["patient_id", "scrambled_meds"]
    merged["patient_id"] = merged["patient_id"].apply(normalize_patient_id)

    identity_for_merge = identity[["patient_id", "age"]].copy()
    identity_for_merge["patient_id"] = identity_for_merge["patient_id"].apply(normalize_patient_id)

    merged = merged.merge(identity_for_merge, on="patient_id", how="left")
    merged["decrypted_meds"] = merged.apply(
        lambda row: decrypt_med(row["scrambled_meds"], row["age"]), axis=1
    )
    return merged[["patient_id", "scrambled_meds", "decrypted_meds"]]


def triage_status(bpm: float) -> str:
    if pd.isna(bpm):
        return "UNKNOWN"
    return "CRITICAL" if bpm < 60 or bpm > 100 else "STABLE"


def main() -> None:
    st.set_page_config(page_title="Project Lazarus - Forensic Dashboard", layout="wide")
    st.title("🧬 Project Lazarus: Medical Forensic Recovery")

    with st.sidebar:
        st.header("Data Source")
        st.write("Place CSV files in `./data`:")
        st.code("patient_demographics.csv\ntelemetry_logs.csv\nprescription_audit.csv")

    try:
        data = load_lazarus_data()
    except FileNotFoundError as err:
        st.error(str(err))
        st.stop()

    identity = prepare_identity_cards(data.demographics)
    telemetry = prepare_telemetry(data.telemetry)
    pharmacy = prepare_pharmacy(data.prescriptions, identity)

    patient_ids = sorted(identity["patient_id"].dropna().astype(str).unique().tolist())
    selected = st.selectbox("Select Patient ID", patient_ids) if patient_ids else None

    if selected is None:
        st.warning("No patient IDs found in demographics data.")
        st.stop()

    # Patient card
    st.subheader("Patient Identity Card")
    card = identity[identity["patient_id"].astype(str) == selected].head(1)
    c1, c2, c3 = st.columns(3)
    c1.metric("Decoded Name", card["decoded_name"].iloc[0] if not card.empty else "Unknown")
    c2.metric("Age", str(card["age"].iloc[0]) if not card.empty else "Unknown")
    c3.metric("Ward", card["ward"].iloc[0] if not card.empty else "Unknown")

    # Vitals monitor
    st.subheader("Vitals Integrity Monitor")
    ptele = telemetry[telemetry["patient_id"].astype(str) == selected].copy()

    if ptele.empty:
        st.info("No telemetry available for selected patient.")
    else:
        latest_bpm = ptele["decoded_bpm"].dropna().iloc[-1] if not ptele["decoded_bpm"].dropna().empty else np.nan
        status = triage_status(latest_bpm)

        if status == "CRITICAL":
            st.markdown(
                "<div style='background:#8B0000;color:white;padding:12px;border-radius:8px;"
                "font-weight:bold;text-align:center;'>🔴 CRITICAL TRIAGE ALERT: BPM OUTSIDE SAFE RANGE (60-100)</div>",
                unsafe_allow_html=True,
            )

        chart = ptele[["timestamp", "decoded_bpm", "interpolated_oxygen"]].rename(
            columns={"decoded_bpm": "BPM", "interpolated_oxygen": "Oxygen"}
        )
        st.line_chart(chart.set_index("timestamp"), height=320)

    # Pharmacy portal
    st.subheader("Pharmacy Portal")
    pmed = pharmacy[pharmacy["patient_id"].astype(str) == selected]
    st.dataframe(pmed, use_container_width=True, hide_index=True)

    with st.expander("Raw Data Diagnostics"):
        st.write("Demographics columns:", list(normalize_columns(data.demographics).columns))
        st.write("Telemetry columns:", list(normalize_columns(data.telemetry).columns))
        st.write("Prescription columns:", list(normalize_columns(data.prescriptions).columns))


if __name__ == "__main__":
    main()
