"""Tensor 회로도·그래프 헬퍼 (schemdraw + matplotlib).

원서·강의록의 그림은 이미지로 잘라 붙이지 않고 이 헬퍼로 다시 그린다.
모든 함수는 SVG를 저장하고 경로를 돌려준다.

    import sys; sys.path.insert(0, "<skill>/scripts")
    from circuits import *
    d = drawing()
    d += (src := elm.SourceV().up().label("12 V", loc="top"))
    ...
    save(d, "fig/ex01.svg")

자주 나오는 1·2차 회로 토폴로지는 아래 builder 함수로 바로 만들 수 있다.
"""
import os
import schemdraw
import schemdraw.elements as elm
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ACCENT = "#6B3FD4"   # tensor.css 의 --p 와 맞출 것
INK = "#1d1d1f"
U = 2.4              # 소자 기본 길이

__all__ = ["elm", "drawing", "save", "out_terms", "plot_response",
           "switched_divider_rc", "switched_series_rl", "lc_lowpass",
           "rc_noninverting", "two_stage", "ACCENT", "INK", "U"]


def drawing(fontsize=12):
    d = schemdraw.Drawing(show=False)
    d.config(unit=U, fontsize=fontsize, lw=1.1, color=INK, font="Noto Sans CJK KR")
    return d


def save(d, path):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    d.save(path)
    return path


def out_terms(d, top, bot, label="$v_o(t)$", length=1.0):
    """출력 단자 두 개와 + / 라벨 / – 표시."""
    d += elm.Line().at(top).right(length)
    t1 = d.here
    d += elm.Dot(open=True)
    d += elm.Line().at(bot).right(length)
    d += elm.Dot(open=True)
    b1 = d.here
    d += elm.Label().at((t1[0], t1[1] - 0.45)).label("+", fontsize=12)
    d += elm.Label().at((b1[0], b1[1] + 0.45)).label("–", fontsize=12)
    d += elm.Label().at((t1[0] + 0.25, (t1[1] + b1[1]) / 2)).label(label, halign="left")


def _switch_over(d, A, action):
    d += elm.Line().at(A).up(1.0)
    d += elm.Switch(action=action).right().label("$t=0$", loc="bot", ofst=0.05)
    d += elm.Line().down(1.0)


# ---------------------------------------------------------------- builders
def switched_divider_rc(path, src="24 V", r_sw="18 Ω", r_sh="4 Ω", r_ret=None,
                        c="$C$", action="close", out="$v_o(t)$", dead=False, rth_note=None, switch=True):
    """전원 - (스위치∥R_sw) - 노드 - R_sh 접지 - C 출력. r_ret 가 있으면 아래 귀환선에 저항.
    dead=True 이면 전원을 끈(단락) 회로를 ACCENT 색으로 그린다 (시험적 해법용).
    switch=False 이면 스위치 없이 R_sw 를 직렬 저항으로만 그린다."""
    d = drawing()
    if dead:
        d += (s := elm.Line().up())
        d += elm.Label().at((s.start[0] - 0.7, (s.start[1] + s.end[1]) / 2)).label("전원 끔\n(단락)", fontsize=9, color="#888", halign="right")
    else:
        d += (s := elm.SourceV().up().label(src, loc="top"))
    A = s.end
    d += elm.Dot().at(A)
    if dead:
        sw_closed_after = action == "close"
        if sw_closed_after:
            d += (r := elm.Line().right().label("단락(스위치 닫힘)", loc="top", fontsize=9, color="#888"))
        else:
            d += (r := elm.Resistor().right().label(r_sw, loc="bot").color(ACCENT))
    else:
        d += (r := elm.Resistor().right().label(r_sw, loc="bot" if switch else "top"))
        if switch:
            _switch_over(d, A, action)
    B = r.end
    d += elm.Dot().at(B)
    col = ACCENT if dead else INK
    d += (rs := elm.Resistor().at(B).down().label(r_sh, loc="bot").color(col))
    D = rs.end
    d += elm.Dot().at(D)
    d += elm.Line().at(B).right(U * 0.9)
    E = d.here
    d += elm.Dot()
    d += (cc := elm.Capacitor().down().label(c, loc="bot"))
    F = cc.end
    d += elm.Dot().at(F)
    if r_ret:
        d += (rr := elm.Resistor().at(s.start).right().label(r_ret, loc="bot").color(col))
        d += elm.Line().at(rr.end).to(F)
    else:
        d += elm.Line().at(s.start).to(F)
    if dead:
        if rth_note:
            d += elm.Label().at((E[0] + 0.9, (E[1] + F[1]) / 2)).label(rth_note, color=ACCENT, halign="left")
    else:
        out_terms(d, E, F, label=out, length=0.8)
    return save(d, path)


def switched_series_rl(path, src="24 V", r1="$R_1$", r2="$R_2$", rl="6 Ω", l="$L$", action="close"):
    """전원 - (스위치∥R1) - R2 - 부하 R(출력) - L 귀환."""
    d = drawing()
    d += (s := elm.SourceV().up().label(src, loc="top"))
    A = s.end
    d += elm.Dot()
    d += (ra := elm.Resistor().right().label(r1, loc="bot"))
    M = ra.end
    d += elm.Dot()
    _switch_over(d, A, action)
    d += (rb := elm.Resistor().at(M).right().label(r2, loc="bot"))
    B = rb.end
    d += elm.Dot()
    d += (ro := elm.Resistor().down().label(rl, loc="bot"))
    D = ro.end
    d += elm.Dot()
    d += elm.Inductor().at(D).to(s.start).label(l, loc="top")
    d += elm.Label().at(((D[0] + s.start[0]) / 2 + 0.9, D[1] - 0.45)).label("$\\leftarrow i(t)$", fontsize=11)
    out_terms(d, B, D)
    return save(d, path)


def lc_lowpass(path, src="$V_1(s)$", l="$Ls$", r="$R$", c="$\\frac{1}{Cs}$", out="$V_o(s)$", series_r=None):
    """전원 - (R1) - L - (R ∥ C) 출력."""
    d = drawing()
    d += (s := elm.SourceV().up().label(src, loc="top"))
    if series_r:
        d += elm.Resistor().right().label(series_r, loc="top")
    d += elm.Inductor().right().label(l, loc="top")
    B = d.here
    d += elm.Dot()
    d += (rr := elm.Resistor().down().label(r, loc="top"))
    D = rr.end
    d += elm.Dot()
    d += elm.Line().at(D).to(s.start)
    d += elm.Line().at(B).right(U * 1.2)
    E = d.here
    d += (cc := elm.Capacitor().down().label(c, loc="bot"))
    d += elm.Line().at(cc.end).to(D)
    out_terms(d, E, cc.end, label=out, length=2.3)
    return save(d, path)


def rc_noninverting(path, src="$v_s(t)$", r1="$R_1$", c="$C$", rf="$R_2$", rg="1 kΩ"):
    """R1-C 저역통과 후 비반전 증폭기, 출력은 (Rf + Rg) 양단."""
    d = drawing()
    d += (s := elm.SourceV().up().label(src, loc="top"))
    d += elm.Line().up(0.6)
    d += (ra := elm.Resistor().right().label(r1, loc="top"))
    N = ra.end
    d += elm.Dot()
    d += (cc := elm.Capacitor().down().toy(s.start).label(c, loc="bot"))
    G = cc.end
    d += elm.Label().at((N[0] - 0.55, (N[1] + G[1]) / 2)).label("$v(t)$", fontsize=11)
    d += elm.Label().at((N[0] - 0.35, N[1] - 0.5)).label("+", fontsize=11)
    d += elm.Label().at((N[0] - 0.35, G[1] + 0.5)).label("–", fontsize=11)
    d += elm.Dot()
    d += elm.Line().at(G).to(s.start)
    d += (op := elm.Opamp(leads=True).flip().anchor("in2").at((N[0] + 2.8, N[1])).right())
    d += elm.Line().at(N).to(op.in2)
    d += elm.Line().at(op.out).right(0.9)
    O = d.here
    d += elm.Dot()
    hh = (O[1] - G[1]) / 2
    d += (r2 := elm.Resistor().down(hh).label(rf, loc="bot"))
    J = r2.end
    d += elm.Dot()
    d += (rk := elm.Resistor().down(hh).label(rg, loc="bot"))
    d += elm.Line().at(rk.end).to(G)
    d += elm.Line().at(J).tox(op.in1[0])
    d += elm.Line().toy(op.in1)
    d += elm.Line().at(O).right(1.1)
    T = d.here
    d += elm.Dot(open=True)
    d += elm.Line().at(rk.end).tox(T[0])
    Bt = d.here
    d += elm.Dot(open=True)
    d += elm.Label().at((T[0], T[1] - 0.45)).label("+", fontsize=12)
    d += elm.Label().at((Bt[0], Bt[1] + 0.45)).label("–", fontsize=12)
    d += elm.Label().at((T[0] + 0.25, (T[1] + Bt[1]) / 2)).label("$v_o(t)$", halign="left")
    return save(d, path)


def two_stage(path, src="$v_i(t)$", l="$L$", r1="$R_1$", gain="$kv_a(t)$", r2="$R_2$", c="$C$"):
    """L-R1 (v_a) 1단 + 종속전압원 kv_a - R2 - C (v_o) 2단."""
    d = drawing()
    d += (s := elm.SourceV().up().label(src, loc="top"))
    d += elm.Inductor().right().label(l, loc="top")
    B = d.here
    d += (rr := elm.Resistor().down().label(["+", "$v_a(t)$", "–"], loc="bot", ofst=0.2).label(r1, loc="top"))
    d += elm.Line().at(rr.end).to(s.start)
    x0 = B[0] + 3.6
    d += (ds := elm.SourceControlledV().at((x0, s.start[1])).up().label(gain, loc="top"))
    d += elm.Resistor().right().label(r2, loc="top")
    E = d.here
    d += elm.Dot()
    d += (cc := elm.Capacitor().down().label(c, loc="bot"))
    d += elm.Line().at(cc.end).to(ds.start)
    out_terms(d, E, cc.end, length=0.8)
    return save(d, path)


# ---------------------------------------------------------------- plots
def plot_response(path, f, tmax, ylim, yticks, xticks, pre=None, marks=(), ylabel="$v_o(t)$, V",
                  size=(2.9, 1.9)):
    """응답 그래프. f(t) 는 t>=0 구간, pre 는 t<0 의 일정값."""
    fig, ax = plt.subplots(figsize=size, dpi=200)
    t = np.linspace(0, tmax, 400)
    ax.plot(t, f(t), color=ACCENT, lw=1.6)
    if pre is not None:
        ax.plot([-tmax * 0.12, 0], [pre, pre], color=ACCENT, lw=1.6)
    for (x, y, lab) in marks:
        ax.plot([x], [y], "o", ms=3, color=INK)
        ax.annotate(lab, (x, y), textcoords="offset points", xytext=(4, -10), fontsize=7)
    ax.set_xlim(-tmax * 0.12, tmax)
    ax.set_ylim(*ylim)
    ax.set_yticks(yticks)
    ax.set_xticks(xticks)
    ax.tick_params(labelsize=7, length=2)
    for sp in ["top", "right"]:
        ax.spines[sp].set_visible(False)
    ax.spines["left"].set_position(("data", 0))
    ax.set_xlabel("$t$ (s)", fontsize=7, loc="right", labelpad=0)
    ax.set_ylabel(ylabel, fontsize=7, rotation=0, loc="top", labelpad=-8)
    ax.grid(alpha=0.25, lw=0.4)
    fig.tight_layout(pad=0.2)
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    fig.savefig(path)
    plt.close(fig)
    return path
