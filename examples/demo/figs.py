"""데모 그림 생성: python3 figs.py  (fig/ 폴더에 SVG 저장)"""
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "../../tensor/scripts"))
from circuits import *
import numpy as np
F = os.path.join(HERE, "fig")

switched_divider_rc(f"{F}/ex01.svg", src="30 V", r_sw="15 Ω", r_sh="6 Ω", r_ret="3 Ω")
switched_divider_rc(f"{F}/ex01_dead.svg", r_sw="15 Ω", r_sh="6 Ω", r_ret="3 Ω", dead=True,
                    rth_note="$R_{th}=6\\parallel 3=2\\,\\Omega$")
switched_series_rl(f"{F}/ex02.svg", src="36 V", rl="9 Ω")
lc_lowpass(f"{F}/ex03.svg")
lc_lowpass(f"{F}/l04.svg", src="$v_i(t)$", series_r="$R_1=10\\,\\Omega$", l="$L=1$ H",
           r="$R_2=10\\,\\Omega$", c="$C=0.05$ F", out="$v_c(t)$")
switched_divider_rc(f"{F}/a01.svg", src="24 V", r_sw="$R$", r_sh="4 Ω", action="open")
switched_divider_rc(f"{F}/a02.svg", src="$4+16u(t)$ V", r_sw="$R_1$", r_sh="20 Ω", switch=False, out="$v(t)$")
rc_noninverting(f"{F}/a03.svg", c="$C=10\\,\\mu$F")
two_stage(f"{F}/a04.svg")
plot_response(f"{F}/a02_plot.svg", lambda t: 10 - 8 * np.exp(-2 * t), 3, (0, 11.5), [2, 10], [1],
              pre=2, marks=[(1, 10 - 8 * np.exp(-2), "8.92")], ylabel="$v(t)$, V")

# s영역 회로 (EX01 원서적 해법) — builder 없이 직접 그리는 예
d = drawing()
d += (s := elm.SourceV().up().label("$\\frac{30}{s}$", loc="top"))
A = s.end
d += elm.Line().right(U)
B = d.here
d += elm.Dot()
d += (r6 := elm.Resistor().down().label("6 Ω", loc="bot"))
D = r6.end
d += elm.Dot()
d += elm.Line().at(B).right(U)
E = d.here
d += elm.Dot()
d += elm.Capacitor().down(U / 2).label("$\\frac{1}{Cs}$", loc="bot")
d += elm.SourceV().down(U / 2).reverse().label("$\\frac{7.5}{s}$", loc="bot")
Fp = d.here
d += elm.Dot()
d += (r3 := elm.Resistor().at(s.start).right().label("3 Ω", loc="bot"))
d += elm.Line().at(r3.end).to(Fp)
d += elm.Label().at(((A[0] + B[0]) / 2, (A[1] + D[1]) / 2)).label("$\\circlearrowright I_1$")
d += elm.Label().at(((B[0] + E[0]) / 2, (A[1] + D[1]) / 2)).label("$\\circlearrowright I_2$")
out_terms(d, E, Fp, label="$V_o(s)$")
save(d, f"{F}/ex01_s.svg")
print("ok")
