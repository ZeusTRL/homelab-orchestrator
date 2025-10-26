from jinja2 import Environment, FileSystemLoader
from pathlib import Path
from ..schemas.device import GenJuniperConfigIn


TEMPLATES = Path(__file__).resolve().parents[1] / "templates" / "juniper"
CONFIG_DIR = Path("/configs")
CONFIG_DIR.mkdir(parents=True, exist_ok=True)


env = Environment(loader=FileSystemLoader(str(TEMPLATES)))


def render_juniper_config(p: GenJuniperConfigIn) -> tuple[str, str]:
    tpl_name = "ex_set_vlans.j2" if p.style == "set" else "ex_hier_vlans.j2"
    tpl = env.get_template(tpl_name)
    text = tpl.render(
        hostname=p.hostname,
        mgmt_ip=p.mgmt_ip,
        vlans=p.vlans,
        uplink_if=p.uplink_if,
        trunk_ifs=p.trunk_ifs,
        access_ports=p.access_ports,
    ).strip() + "\n"
    out_path = CONFIG_DIR / f"{p.hostname}.conf"
    out_path.write_text(text)
    return text, str(out_path)