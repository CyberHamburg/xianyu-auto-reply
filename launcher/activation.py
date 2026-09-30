"""
֤ģ

ܣ
1. ݻ + ʱɴЧڵļ
2. ֤Ƿƥ䵱ǰδ
3. /ȡ֤ļʱ䣩
4. ṩʱѯӿڹGUIʾ
"""
import hashlib
import json
import os
import secrets
from datetime import datetime, timezone, timedelta
from pathlib import Path

# õԿֵ
_SECRET_SALT = "XianyuAutoReply@2024#Lic"

# ֤ļ
_LICENSE_FILE = "license.dat"

# ʱʱ
_BJ_TZ = timezone(timedelta(hours=8))


def _get_license_path() -> Path:
    """
    ȡ֤ļ·

    ֤ļexeͬĿ¼ĿĿ¼µdataļ

    Returns:
        ֤ļ·
    """
    from launcher.frozen_detect import get_project_root
    base_dir = get_project_root()
    data_dir = base_dir / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir / _LICENSE_FILE


def _now_bj() -> datetime:
    """ȡǰʱ"""
    return datetime.now(_BJ_TZ)


def calc_expire_time(unit: str, amount: int) -> int:
    """
    άȺ㵽ʱʱ䣩

    Args:
        unit: ʱάȣh=Сʱ d= m= y=
        amount: Ϊ
    Returns:
        ʱUnixʱ룩
    """
    now = _now_bj()
    if unit == "h":
        expire = now + timedelta(hours=amount)
    elif unit == "d":
        expire = now + timedelta(days=amount)
    elif unit == "m":
        # ·ݼ򵥴ÿ°30
        expire = now + timedelta(days=amount * 30)
    elif unit == "y":
        expire = now + timedelta(days=amount * 365)
    else:
        raise ValueError(f"ֵ֧ʱά: {unit}ѡ: h/d/m/y")
    return int(expire.timestamp())


def generate_activation_code(machine_id: str, expire_ts: int) -> str:
    """
    ݻ͵ʱɼ

    ʽ: {ʱhexд}-{ǩ16λд}
    ǩ = SHA256(:ʱ:) ȡǰ16λ

    Args:
        machine_id: 32λд
        expire_ts: ʱUnixʱ룩
    Returns:
        ַʽ "67E3A1B0-A1B2C3D4E5F67890"
    """
    expire_hex = format(expire_ts, "X")
    sig = hashlib.sha256(
        f"{machine_id}:{expire_ts}:{_SECRET_SALT}".encode("utf-8")
    ).hexdigest()[:16].upper()
    return f"{expire_hex}-{sig}"


def verify_activation_code(machine_id: str, activation_code: str) -> dict:
    """
    ֤Ƿƥ룬ȡʱ

    Args:
        machine_id: 32λд
        activation_code: ַ
    Returns:
        ֵ:
        - valid: bool ǩǷЧ
        - expire_ts: int ʱǩЧʱΪ0
        - expired: bool Ƿѹ
    """
    code = activation_code.strip().upper()
    parts = code.split("-")
    if len(parts) != 2:
        return {"valid": False, "expire_ts": 0, "expired": True}

    try:
        expire_ts = int(parts[0], 16)
    except ValueError:
        return {"valid": False, "expire_ts": 0, "expired": True}

    expected_sig = hashlib.sha256(
        f"{machine_id}:{expire_ts}:{_SECRET_SALT}".encode("utf-8")
    ).hexdigest()[:16].upper()

    if parts[1] != expected_sig:
        return {"valid": False, "expire_ts": 0, "expired": True}

    now_ts = int(_now_bj().timestamp())
    return {
        "valid": True,
        "expire_ts": expire_ts,
        "expired": now_ts > expire_ts,
    }


def save_license(machine_id: str, activation_code: str,
                 expire_ts: int, used_renew_codes: list = None,
                 last_renew_ts: int = 0) -> bool:
    """
    漤Ϣ֤ļ

    Args:
        machine_id: 32λд
        activation_code: 
        expire_ts: ʱ
        used_renew_codes: ʹõбѡ
        last_renew_ts: ϴʱѡһֻһεУ飩
    Returns:
        TrueɹFalseʧ
    """
    try:
        check_hash = hashlib.sha256(
            f"{machine_id}:{activation_code}:{expire_ts}:{_SECRET_SALT}"
            .encode("utf-8")
        ).hexdigest()[:16].upper()

        data = {
            "machine_id": machine_id,
            "activation_code": activation_code.upper(),
            "expire_ts": expire_ts,
            "check_hash": check_hash,
            "used_renew_codes": used_renew_codes or [],
            "last_renew_ts": last_renew_ts,
        }
        license_path = _get_license_path()
        license_path.write_text(
            json.dumps(data, indent=2), encoding="utf-8"
        )
        return True
    except Exception:
        return False


def load_and_verify_license(current_machine_id: str) -> dict:
    """
    ֤ļУ鼤״̬

    ݣļԡ۸Ĺϣƥ䡢
    ǩǷѹڡ

    Args:
        current_machine_id: ǰĻ
    Returns:
        ֵ:
        - valid: bool Ƿ񼤻Чǩȷδڣ
        - message: str ״̬˵
        - machine_changed: bool Ƿ仯
        - expire_ts: int ʱ0ʾδ֪
        - expired: bool Ƿѹ
    """
    license_path = _get_license_path()
    _fail = {"valid": False, "machine_changed": False,
             "expire_ts": 0, "expired": False}

    if not license_path.exists():
        return {**_fail, "message": "δҵļ뼤"}

    try:
        data = json.loads(license_path.read_text(encoding="utf-8"))
    except Exception:
        return {**_fail, "message": "ļ𻵣¼"}

    stored_mid = data.get("machine_id", "")
    stored_code = data.get("activation_code", "")
    stored_expire = data.get("expire_ts", 0)
    stored_hash = data.get("check_hash", "")

    # Уļԣ۸ģ
    expected_hash = hashlib.sha256(
        f"{stored_mid}:{stored_code}:{stored_expire}:{_SECRET_SALT}"
        .encode("utf-8")
    ).hexdigest()[:16].upper()

    if stored_hash != expected_hash:
        return {**_fail, "message": "ļѱ۸ģ¼"}

    # 루ͬݣͬɷʽµõĺѡ룩
    try:
        from launcher.hardware_id import generate_machine_id_candidates
        candidates = set(generate_machine_id_candidates())
        candidates.add(current_machine_id)
    except Exception:
        candidates = {current_machine_id}

    if stored_mid not in candidates:
        return {**_fail, "message": "⵽Ӳѱ仯¼",
                "machine_changed": True}

    # ֤ǩ license д洢 machine_idǩ֮󶨣
    result = verify_activation_code(stored_mid, stored_code)
    if not result["valid"]:
        return {**_fail, "message": "Ч"}

    # Ƿ
    if result["expired"]:
        expire_str = format_expire_time(result["expire_ts"])
        return {**_fail, "message": f"ѹڣ{expire_str}ϵͳ",
                "expire_ts": result["expire_ts"], "expired": True}

    return {
        "valid": True,
        "message": "֤ͨ",
        "machine_changed": False,
        "expire_ts": result["expire_ts"],
        "expired": False,
    }


def calc_duration_seconds(unit: str, amount: int) -> int:
    """
    άȺʱ

    Args:
        unit: ʱάȣh=Сʱ d= m= y=
        amount: Ϊ
    Returns:
        ʱ
    """
    if unit == "h":
        return amount * 3600
    elif unit == "d":
        return amount * 86400
    elif unit == "m":
        return amount * 30 * 86400
    elif unit == "y":
        return amount * 365 * 86400
    else:
        raise ValueError(f"ֵ֧ʱά: {unit}ѡ: h/d/m/y")


def _build_renew_signature(machine_id: str, duration_seconds: int, issue_marker: str | None = None) -> str:
    if issue_marker is None:
        payload = f"{machine_id}:R:{duration_seconds}:{_SECRET_SALT}"
    else:
        payload = f"{machine_id}:R:{duration_seconds}:{issue_marker}:{_SECRET_SALT}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16].upper()


def generate_renew_code(machine_id: str, duration_seconds: int) -> str:
    """
    ڼ루Rͷͨ룩

    ʽ: R{ʱhexд}-{ǩ16λд}
    ǩ = SHA256(:R:ʱ:) ȡǰ16λ

    Args:
        machine_id: 32λд
        duration_seconds: Ҫڵʱ룩
    Returns:
        ַʽ "R278D00-A1B2C3D4E5F67890"
    """
    issue_marker = secrets.token_hex(8).upper()
    dur_hex = format(duration_seconds, "X")
    sig = _build_renew_signature(machine_id, duration_seconds, issue_marker)
    return f"R{dur_hex}-{issue_marker}-{sig}"


def verify_renew_code(machine_id: str, renew_code: str) -> dict:
    """
    ֤ڼǷƥ룬ȡʱ

    Args:
        machine_id: 32λд
        renew_code: ַRͷ
    Returns:
        ֵ:
        - valid: bool ǩǷЧ
        - duration_seconds: int ʱЧʱΪ0
    """
    code = renew_code.strip().upper()
    if not code.startswith("R"):
        return {"valid": False, "duration_seconds": 0}

    # ȥRǰ׺
    body = code[1:]
    parts = body.split("-")
    if len(parts) not in (2, 3):
        return {"valid": False, "duration_seconds": 0}

    try:
        duration_seconds = int(parts[0], 16)
    except ValueError:
        return {"valid": False, "duration_seconds": 0}

    if len(parts) == 2:
        expected_sig = _build_renew_signature(machine_id, duration_seconds)
        actual_sig = parts[1]
    else:
        issue_marker = parts[1].strip().upper()
        if not issue_marker:
            return {"valid": False, "duration_seconds": 0}
        try:
            int(issue_marker, 16)
        except ValueError:
            return {"valid": False, "duration_seconds": 0}
        expected_sig = _build_renew_signature(machine_id, duration_seconds, issue_marker)
        actual_sig = parts[2]

    if actual_sig != expected_sig:
        return {"valid": False, "duration_seconds": 0}

    return {"valid": True, "duration_seconds": duration_seconds}


def _load_used_renew_codes() -> list:
    """
    ֤ļмʹõб

    Returns:
        ʹַбļڻʧܷؿб
    """
    license_path = _get_license_path()
    if not license_path.exists():
        return []
    try:
        data = json.loads(license_path.read_text(encoding="utf-8"))
        return data.get("used_renew_codes", [])
    except Exception:
        return []


def _load_last_renew_ts() -> int:
    """
    ֤ļмϴʱ

    Returns:
        ϴڵUnixʱļڻ޼¼0
    """
    license_path = _get_license_path()
    if not license_path.exists():
        return 0
    try:
        data = json.loads(license_path.read_text(encoding="utf-8"))
        return data.get("last_renew_ts", 0)
    except Exception:
        return 0


def renew_license(machine_id: str, renew_code: str) -> dict:
    """
    ʹмڣʱӵԭʱ䣩

    Args:
        machine_id: 32λд
        renew_code: ַ
    Returns:
        ֵ:
        - success: bool Ƿɹ
        - message: str ˵
        - new_expire_ts: int µĵʱʧʱΪ0
    """
    # ֤
    code_upper = renew_code.strip().upper()
    verify_result = verify_renew_code(machine_id, code_upper)
    if not verify_result["valid"]:
        return {"success": False, "message": "ЧǷȷ",
                "new_expire_ts": 0}

    duration = verify_result["duration_seconds"]

    # صǰϢ
    license_result = load_and_verify_license(machine_id)
    old_expire_ts = license_result.get("expire_ts", 0)

    # ǷѾʹù
    used_codes = _load_used_renew_codes()
    if code_upper in used_codes:
        return {"success": False, "message": "ʹùظʹ",
                "new_expire_ts": 0}

    # һֻһ
    last_renew = _load_last_renew_ts()
    if last_renew > 0:
        now_ts = int(_now_bj().timestamp())
        elapsed = now_ts - last_renew
        if elapsed < 86400:
            remaining_hours = (86400 - elapsed) // 3600
            remaining_mins = ((86400 - elapsed) % 3600) // 60
            return {"success": False,
                    "message": f"ÿֻһΣ{remaining_hours}Сʱ{remaining_mins}Ӻ",
                    "new_expire_ts": 0}

    if old_expire_ts <= 0:
        # ûЧ¼ӵǰʱ俪ʼ
        base_ts = int(_now_bj().timestamp())
    elif license_result.get("expired", False):
        # ѹڣӵǰʱ俪ʼ
        base_ts = int(_now_bj().timestamp())
    else:
        # δڣӵԭʱ
        base_ts = old_expire_ts

    new_expire_ts = base_ts + duration

    # µͨ루µĵʱ䣩
    new_code = generate_activation_code(machine_id, new_expire_ts)

    # ¼ʹõͱʱ䲢
    used_codes.append(code_upper)
    current_ts = int(_now_bj().timestamp())
    if not save_license(machine_id, new_code, new_expire_ts, used_codes,
                        last_renew_ts=current_ts):
        return {"success": False, "message": "漤Ϣʧ",
                "new_expire_ts": 0}

    expire_str = format_expire_time(new_expire_ts)
    return {"success": True,
            "message": f"ڳɹµʱ: {expire_str}",
            "new_expire_ts": new_expire_ts}


def revoke_license() -> dict:
    """
    ע״̬ɾ֤ļ

    Returns:
        ֵ:
        - success: bool עǷɹ
        - message: str ˵
    """
    license_path = _get_license_path()
    if not license_path.exists():
        return {"success": False, "message": "ǰûм¼"}
    try:
        license_path.unlink()
        return {"success": True, "message": "ע¼"}
    except Exception as e:
        return {"success": False, "message": f"עʧ: {e}"}


def format_expire_time(expire_ts: int) -> str:
    """
    ʱʽΪʱַ

    Args:
        expire_ts: Unixʱ
    Returns:
        ʽַ "2026-03-30 18:00:00"
    """
    if expire_ts <= 0:
        return "δ֪"
    dt = datetime.fromtimestamp(expire_ts, tz=_BJ_TZ)
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def get_remaining_text(expire_ts: int) -> str:
    """
    ʣʱ䲢ؿɶı

    Args:
        expire_ts: ʱ
    Returns:
        ʣʱı "ʣ 312Сʱ"  "ѹ"
    """
    if expire_ts <= 0:
        return "δ֪"
    now_ts = int(_now_bj().timestamp())
    diff = expire_ts - now_ts
    if diff <= 0:
        return "ѹ"

    days = diff // 86400
    hours = (diff % 86400) // 3600
    minutes = (diff % 3600) // 60

    if days > 0:
        return f"ʣ {days}{hours}Сʱ"
    elif hours > 0:
        return f"ʣ {hours}Сʱ{minutes}"
    else:
        return f"ʣ {minutes}"
