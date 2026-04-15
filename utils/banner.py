import base64
import hashlib
import zlib


_PAYLOAD_KEY = b"ZhongBannerKey"
_ENC_PAYLOAD = (
    "BC_H;DlNKLcH5a8bw!iI%nJG8IcpNF_1$9$he#RU0SiHf?bphJ!B~hh?M~oc7c^PXvCCw<+Q}^M`IryW!e(%<s=Wgmg)x5zE8IfDKR!f^BvgQzEPj2z>gKvGH1%g?#Id#$>1khwi!_Jp+GbiqE2?qgSL^Glw&8qa3v7(5{>a0~1n`shiMNFr3zBD^h3()<sj$bz!LxLxTw~^HEVPr4poiR<0FBQPmj-~Gwy@FvkdvF?2=v~|iqQQ&IVYb@sRfOIjE6E=;hek5YcOvgQx3oVc*bV5B-{eQkgse>-P6Y^68w47q0_RQ+`4z#t0A4Q2)mnX)RQH^fz#yM0DR=vy_Cf(7znMAB-_xXZbjRIK2NrsIWsW$+{KRC!}xpv%()TOpO?}C=e;6#xtybKHWqsdth}R}q`gp8ju7;j0x^(-hpm={tR0>c5t9nJs-lyDfceP0-Bb}5hqqL%ZbdIo_lqL$T`xkaUq0Q`!3OCKVmj4MVe9=^X7(K*=@GbnW{cX#eh)3n`44GQ7E*`lv3lz0#HmZ>=uu;&%lxIoR5<p^ehs0w6NelwtW%;m^x<qO<Nrc4bjWeSQF30NW?I?f`GytzqAWL)`aa7IUsw`4>k**k*>G)te_NkMKBT|_4<*&HH$?Ol$s$4g$TIaPdsprV!U!X(QLb%4KpP<>D`s4YTy>}KT(g`R_ae@pqdTrvAH;p)i_T;_V<2j8?OWT=6gMxaYz!}Anu3*6l*0Oe+H_dP`n73sdge`cXGil3uS85G7Crhf8cJLJd`GQEa<OBpucZTGEH4UCfM-5519VVJ0dp>DeVOLGbcvl@6QMaUOj6R6rurjz?$0sTfGK*OI@D0u$ogi8T#T7Ka344&s<Cky_?Ler@MPQZ6XTVFAFw5S^wL`}BA6YRJ@Wj2d{Xqv@{L*|5W^<pk{o8M73oVydMO_T)Xiq=aB8YJCEF_>>EZFU&+A=$p;2ADj~h^@v2|?XDk8#c`-jWV1w7$Wp$zbHDB)gzUZD6|R~L&CmgxR0RXEaOo9y$W)YU%0_jDEl)jn6{5NCirwZOWoU6#ZzFO)dsiMA2e)SsxDMaWi`{*wRtybM6r=9Tz_kBb$XfgYuTS63KCu;{7H)hE-yIgZa53$#)Li^9$}vH9BW><2QN;C(d+o@ptSob-`>K!wpT"
)
_EXPECTED_PAYLOAD_HASH = (
    "2a0fb682ccf41c40ec4fc1030512320746c0d4d542d0971780383049d08d6928"
)


def _decode_payload_source():
    cipher = base64.b85decode(_ENC_PAYLOAD.encode("ascii"))
    compressed = bytes(
        byte ^ _PAYLOAD_KEY[index % len(_PAYLOAD_KEY)]
        for index, byte in enumerate(cipher)
    )
    payload = zlib.decompress(compressed)
    if hashlib.sha256(payload).hexdigest() != _EXPECTED_PAYLOAD_HASH:
        raise RuntimeError("banner payload integrity check failed")
    return payload.decode("utf-8")


_PAYLOAD_NAMESPACE = {}
exec(_decode_payload_source(), _PAYLOAD_NAMESPACE)

STOP_MESSAGE = _PAYLOAD_NAMESPACE["STOP_MESSAGE"]


def get_banner_title():
    return _PAYLOAD_NAMESPACE["get_banner_title"]()


def get_banner_lines():
    return _PAYLOAD_NAMESPACE["get_banner_lines"]()


def build_banner_identity(title, lines):
    return _PAYLOAD_NAMESPACE["build_banner_identity"](title, lines)


def compute_banner_identity_hash(title, lines):
    return _PAYLOAD_NAMESPACE["compute_banner_identity_hash"](title, lines)


def banner_identity_is_valid(title=None, lines=None):
    return _PAYLOAD_NAMESPACE["banner_identity_is_valid"](title, lines)


def generate_banner():
    return _PAYLOAD_NAMESPACE["generate_banner"]()


EXPECTED_BANNER_IDENTITY_HASH = _PAYLOAD_NAMESPACE["EXPECTED_BANNER_IDENTITY_HASH"]
